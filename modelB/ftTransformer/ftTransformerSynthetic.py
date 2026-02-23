import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import ParameterGrid
from sklearn.metrics import r2_score
import json
from tqdm import tqdm

# -------------------------------------------------------
# Define MAPE metric
# -------------------------------------------------------
def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan

    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


# -----------------------------
# Normalize material text into consistent format
# -----------------------------
def normalize_material(x):
    if pd.isna(x):
        return np.nan
    return (
        str(x)
        .lower()
        .strip()
        .replace("_", "-")
        .replace(" ", "-")
    )

# -----------------------------
# Normalize renovation tokens
# -----------------------------
def normalize_token(x):
    return " ".join(x.lower().strip().split())

# -----------------------------
# Parse renovation type column into list format
# Converts string or list string into list format
# -----------------------------
def parse_reno(value):
    if pd.isna(value):
        return []
    value = str(value)
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [normalize_token(v) for v in parsed if isinstance(v, str)]
        except Exception:
            return []
    return [normalize_token(value)]


# -----------------------------
# Preprocess real dataset to match synthetic schema
# -----------------------------
def preprocess_real(df, require_target=False):
    
    if "type_of_renovation" in df.columns:
        # Clean renovation type column
        df["type_of_renovation"] = df["type_of_renovation"].astype(str).str.strip().str.lower()
        df = df[~df["type_of_renovation"].isin(["", "nan", "none", "null"])]

        # Encode material grade ordinally
        material_mapping = {
            "budget-friendly": 0,
            "mid-range": 1,
            "high-end": 2
        }

        df["material_grade"] = df["material_grade"].apply(normalize_material)
        df["material_grade"] = df["material_grade"].map(material_mapping)
        df["material_grade"] = df["material_grade"].astype(float)

    
        # Parse renovation types into structured form
        df["type_of_renovation_parsed"] = df["type_of_renovation"].apply(parse_reno)

        # Create one hot features for renovation types
        fixed_types = {
            "bathroom": "bathroom",
            "bedroom": "bedroom",
            "kitchen": "kitchen",
            "living room": "living_room",
            "other/custom": "other_custom",
            "full renovation": "full_renovation"
        }

        for suffix in fixed_types.values():
            df[f"reno_{suffix}"] = 0

        for key, suffix in fixed_types.items():
            df[f"reno_{suffix}"] = df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))

        # Drop unused columns
        df = df.drop(
            columns=["type_of_renovation", "type_of_renovation_parsed", "Location", "id", "extended_rooms"],
            errors="ignore"
        )

        df["post_renovation_value"] = df["price"]

        # structural_change naming consistency
        if "structural_changes" in df.columns:
            df["structural_change"] = df["structural_changes"].astype(int)

    else:
        # Ensure correct types
        df["material_grade"] = df["material_grade"].astype(float)

        df = df.drop(
            columns=["source_row"],
            errors="ignore"
        )
    return df

# -----------------------------
# config
# -----------------------------

# Column we want to predict
target = "post_renovation_value"

numeric_cols = [
    "property_size",
    "renovation_cost",
    "sqft_renovated",
    "sqft_to_add",
    "material_grade",
    "structural_change",
    "reno_bathroom",
    "reno_bedroom",
    "reno_kitchen",
    "reno_living_room",
    "reno_other_custom",
    "reno_full_renovation",
    "location" 
]


# Hyperparameter search space
param_grid = {
    "d_model": [128, 256],
    "n_layers": [2, 3],
    "learning_rate": [1e-3, 5e-4],
    "weight_decay": [1e-4, 5e-4],
    "dropout": [0.1],
}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -----------------------------
# Load train val data
# -----------------------------
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv").dropna(subset=[target])
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv").dropna(subset=[target])

# Create scalers
feature_scaler = StandardScaler()
target_scaler = StandardScaler()

# Split features and target
X_train = train_exp[numeric_cols].copy()
y_train_raw = train_exp[target].values.astype(np.float32)

X_val = val_exp[numeric_cols].copy()
y_val_raw = val_exp[target].values.astype(np.float32)

# Scale target values
y_train = target_scaler.fit_transform(y_train_raw.reshape(-1, 1)).flatten()
y_val = target_scaler.transform(y_val_raw.reshape(-1, 1)).flatten()

# Scale numeric features
X_train[numeric_cols] = feature_scaler.fit_transform(X_train[numeric_cols])
X_val[numeric_cols] = feature_scaler.transform(X_val[numeric_cols])


# Convert to numpy arrays
X_train_num = X_train[numeric_cols].values.astype(np.float32)
X_val_num = X_val[numeric_cols].values.astype(np.float32)

# Convert to torch tensors
X_train_num_t = torch.tensor(X_train_num, device=device)
y_train_t = torch.tensor(y_train, dtype=torch.float32, device=device)

X_val_num_t = torch.tensor(X_val_num, device=device)
y_val_t = torch.tensor(y_val, dtype=torch.float32, device=device)

# Fix randomness - NN starts with random weights 
torch.set_num_threads(8)
torch.manual_seed(42)
np.random.seed(42)


# =========================================================
# Load synthetic test set
# =========================================================

test_exp = pd.read_csv(
    "processed_data/synthetic_test_expanded.csv"
).dropna(subset=[target])

# Split features and target
X_test = test_exp[numeric_cols].copy()
y_test_raw = test_exp[target].values.astype(np.float32)

# Scale numeric features using TRAIN scaler
X_test[numeric_cols] = feature_scaler.transform(X_test[numeric_cols])


# Convert to numpy
X_test_num = X_test[numeric_cols].values.astype(np.float32)

# Convert to torch tensors
X_test_num_t = torch.tensor(X_test_num, device=device)

# =========================================================
# Define FT Transformer model
# =========================================================
class FTTransformer(nn.Module):
    def __init__(self, num_numeric,
                 d_model=128, n_heads=4, n_layers=3, dropout=0.1):
        super().__init__()

        # Learnable embeddings for numeric features
        self.num_embeddings = nn.Parameter(torch.randn(num_numeric, d_model))
        self.num_bias = nn.Parameter(torch.zeros(num_numeric, d_model))

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=256,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        # CLS token for regression output
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))

        # Final prediction head
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.ReLU(),
            nn.Linear(d_model, 1),
        )

    def forward(self, x_num):
        batch_size = x_num.size(0)

        # Convert numeric features into embeddings
        num_tokens = x_num.unsqueeze(-1) * self.num_embeddings + self.num_bias  # (B, Nnum, D)


        # Combine numeric tokens
        tokens = torch.cat([num_tokens], dim=1)  # (B, Nnum+Ncat, D)

        # Add CLS token
        cls = self.cls_token.expand(batch_size, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)  # (B, 1+Nnum+Ncat, D)

        # Run transformer
        out = self.transformer(tokens)

         # Use CLS output for regression
        return self.head(out[:, 0]).squeeze(-1)

# =========================================================
# Training for one hyperparameter setting
# =========================================================

def train_single_config(params):

    # Create model
    model = FTTransformer(
        num_numeric=X_train_num.shape[1],
        d_model=params["d_model"],
        n_layers=params["n_layers"],
        dropout=params["dropout"],
    ).to(device)

    # Optimizer
    optimizer = optim.AdamW(
        model.parameters(),
        lr=params["learning_rate"],
        weight_decay=params["weight_decay"],
    )

    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    patience = 15
    patience_counter = 0
    best_state_local = None

    # Training loop
    for _ in range(100):
        model.train()
        optimizer.zero_grad()

        preds = model(X_train_num_t)
        loss = criterion(preds, y_train_t)
        loss.backward()
        optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_preds_scaled_t = model(X_val_num_t)
            val_loss = criterion(val_preds_scaled_t, y_val_t)

        val_loss_value = float(val_loss.detach().cpu().item())

        # Save best model
        if val_loss_value < best_val_loss:
            best_val_loss = val_loss_value
            patience_counter = 0
            best_state_local = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= patience:
            break

    if best_state_local is None:
        return None

    # Load best weights
    model.load_state_dict(best_state_local)
    model.eval()

    # Predict on validation set
    with torch.no_grad():
        val_preds_scaled = model(X_val_num_t).detach().cpu().numpy()

    # Convert back to original scale
    val_preds = target_scaler.inverse_transform(
        val_preds_scaled.reshape(-1, 1)
    ).flatten()

    # Aggregate per property
    pred_df = pd.DataFrame({
        "source_row": val_exp["source_row"].values,
        "y_true": y_val_raw,
        "y_pred": val_preds,
    })

    prop_level = pred_df.groupby("source_row", as_index=False).agg(
        y_true=("y_true", "first"),
        y_pred=("y_pred", "mean"),
    )

    # Compute R2
    r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])

    return {
        "params": params,
        "r2": r2,
        "state_dict": best_state_local
    }

# =========================================================
# Grid search
# =========================================================
# results = []
# for params in ParameterGrid(param_grid):
#     result = train_single_config(params)
#     if result is not None:
#         results.append(result)

# # ----------------------------
# # Filter valid results
# # ----------------------------

# results = [r for r in results if r is not None]

# # ----------------------------
# # Select best model
# # ----------------------------

# best_result = max(results, key=lambda x: x["r2"])

# best_params = best_result["params"]
# best_r2 = best_result["r2"]
# best_model_state = best_result["state_dict"]

# print("best R2:", best_r2)
# print("best params:", best_params)

# # =========================================================
# # Save best parameters
# # =========================================================

# params_to_save = {
#     "best_r2": best_r2,
#     "best_params": best_params,
#     "numeric_cols": numeric_cols
# }

# with open("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/ft_transformer_best_params.json", "w") as f:
#     json.dump(params_to_save, f, indent=2)

# print("Saved best parameters to ft_transformer_best_params.json")


# # =========================================================
# # Save best model weights
# # =========================================================

# # Recreate model with best params
# best_model = FTTransformer(
#     num_numeric=X_train_num.shape[1],
#     d_model=best_params["d_model"],
#     n_layers=best_params["n_layers"],
#     dropout=best_params["dropout"],
# ).to(device)

# best_model.load_state_dict(best_model_state)

# # Save model state_dict
# torch.save({
#     "model_state_dict": best_model.state_dict(),
#     "numeric_cols": numeric_cols,
#     "target_scaler_mean": target_scaler.mean_.tolist(),
#     "target_scaler_scale": target_scaler.scale_.tolist(),
#     "feature_scaler_mean": feature_scaler.mean_.tolist(),
#     "feature_scaler_scale": feature_scaler.scale_.tolist(),
# }, "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/ft_transformer_best_model.pt")

# print("Saved best model to ft_transformer_best_model.pt")

# =========================================================
# Load best parameters from file
# =========================================================

with open("modelB/models/ftTransformer/ft_transformer_best_params.json", "r") as f:
    saved_params = json.load(f)

best_params = saved_params["best_params"]

# =========================================================
# Load saved model checkpoint
# =========================================================

checkpoint = torch.load(
    "modelB/models/ftTransformer/ft_transformer_best_model.pt",
    map_location=device
)

# Restore scalers
target_scaler.mean_ = np.array(checkpoint["target_scaler_mean"])
target_scaler.scale_ = np.array(checkpoint["target_scaler_scale"])

feature_scaler.mean_ = np.array(checkpoint["feature_scaler_mean"])
feature_scaler.scale_ = np.array(checkpoint["feature_scaler_scale"])

# Recreate model
final_model = FTTransformer(
    num_numeric=len(checkpoint["numeric_cols"]),
    d_model=best_params["d_model"],
    n_layers=best_params["n_layers"],
    dropout=best_params["dropout"],
).to(device)

# Load weights
final_model.load_state_dict(checkpoint["model_state_dict"])
final_model.eval()

# =========================================================
# Predict on synthetic test set
# =========================================================

# with torch.no_grad():
#     test_preds_scaled = final_model(X_test_num_t).cpu().numpy()

# # Inverse scale target
# test_preds = target_scaler.inverse_transform(
#     test_preds_scaled.reshape(-1, 1)
# ).flatten()

# # Aggregate per property
# pred_df = pd.DataFrame({
#     "source_row": test_exp["source_row"].values,
#     "y_true": y_test_raw,
#     "y_pred": test_preds,
# })

# prop_level = pred_df.groupby("source_row", as_index=False).agg(
#     y_true=("y_true", "first"),
#     y_pred=("y_pred", "mean"),
# )

# # Compute R2
# test_r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])

# # Compute MAPE using your function
# test_mape = mape(
#     prop_level["y_true"].values,
#     prop_level["y_pred"].values
# )

# print("Test R2:", test_r2)
# print("Test MAPE:", test_mape)

# =========================================================
# Predict on real test set
# =========================================================
real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

real_df = preprocess_real(real_df)

y_real = real_df["price"].values.astype(np.float32)

X_real = real_df[numeric_cols].copy()

# scale using TRAIN scaler
X_real[numeric_cols] = feature_scaler.transform(X_real[numeric_cols])

X_real_t = torch.tensor(
    X_real[numeric_cols].values.astype(np.float32),
    device=device
)

with torch.no_grad():
    real_preds_scaled = final_model(X_real_t).cpu().numpy()

real_preds = target_scaler.inverse_transform(
    real_preds_scaled.reshape(-1, 1)
).flatten()

real_r2 = r2_score(y_real, real_preds)
real_mape = mape(y_real, real_preds)

print("Real Test R2:", real_r2)
print("Real Test MAPE:", real_mape)


# -------------------------------------------------------
# Save predictions for Wilcoxon test 
# -------------------------------------------------------
ft_preds_path = "modelB/ftTransformer/fttransformer_train_real_preds.csv"

rf_preds_df = pd.DataFrame({
    "source_row": real_df.index,
    "y_true": y_real,
    "y_pred": real_preds
})


rf_preds_df.to_csv(ft_preds_path, index=False)

