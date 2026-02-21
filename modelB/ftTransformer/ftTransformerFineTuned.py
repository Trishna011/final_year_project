import json
import pandas as pd
import numpy as np
import ast
from sklearn.metrics import r2_score
import random
from sklearn.model_selection import KFold
import torch
from sklearn.preprocessing import StandardScaler
from modelB.ftTransformer.ftTransformerSynthetic import FTTransformer

# -----------------------------
# Helpers
# -----------------------------
def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
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

        # structural_change naming consistency - needed here as you didn't save synth feature cols
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
# Load pretrained synthetic model
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load best params used to build the model architecture
with open("modelB/models/ftTransformer/ft_transformer_best_params.json", "r") as f:
#with open("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/ft_transformer_best_params.json", "r") as f:
    saved_params = json.load(f)

best_params = saved_params["best_params"]

# Load pretrained synthetic model checkpoint
checkpoint = torch.load("modelB/models/ftTransformer/ft_transformer_best_model.pt", map_location=device)
#checkpoint = torch.load("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/ft_transformer_best_model.pt", map_location=device)

numeric_cols = checkpoint["numeric_cols"]

# Rebuild model architecture exactly as used during synthetic training
final_model = FTTransformer(
    num_numeric=len(numeric_cols),
    d_model=int(saved_params["best_params"]["d_model"]),
    n_layers=int(saved_params["best_params"]["n_layers"]),
    dropout=float(saved_params["best_params"]["dropout"])
).to(device)

# Load pretrained synthetic weights
final_model.load_state_dict(checkpoint["model_state_dict"])
final_model.eval()

# -----------------------------
# Prepare train_val set for fine-tuning
# ------------------------------
dev_df = pd.read_csv("processed_data/real_train_val_with_predicted_reno_cost.csv")
#dev_df = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/real_train_val_with_predicted_reno_cost.csv")

# Convert real schema into synthetic-compatible schema
dev_df = preprocess_real(dev_df, require_target=True)

dev_df["post_renovation_value"] = dev_df["price"]

numeric_cols = checkpoint["numeric_cols"]

# Extract features and target
X_dev = dev_df[numeric_cols].copy()
y_dev = dev_df["post_renovation_value"].values.astype(np.float32)

#--------------------
# Restore synthetic scalers
# This ensures real data is scaled exactly like synthetic training
#--------------------

# Create scalers before assigning mean_ and scale_
feature_scaler = StandardScaler()
target_scaler = StandardScaler()

# Restore scalers
feature_scaler.mean_ = np.array(checkpoint["feature_scaler_mean"], dtype=float)
feature_scaler.scale_ = np.array(checkpoint["feature_scaler_scale"], dtype=float)

target_scaler.mean_ = np.array(checkpoint["target_scaler_mean"], dtype=float)
target_scaler.scale_ = np.array(checkpoint["target_scaler_scale"], dtype=float)

# Clean numeric columns
dev_df[numeric_cols] = dev_df[numeric_cols].apply(
    pd.to_numeric
)


# Scale features and target
X_dev_scaled = feature_scaler.transform(X_dev.values.astype(np.float32))

y_dev_scaled = target_scaler.transform(
    y_dev.reshape(-1,1)
).flatten()

X_dev_scaled = X_dev_scaled.astype(np.float32)
y_dev_scaled = y_dev_scaled.astype(np.float32)

# ------------------------
# Convert to tensors
# ------------------------

X_dev_t = torch.tensor(
    X_dev[numeric_cols].values.astype(np.float32),
    device=device
)

y_dev_t = torch.tensor(
    y_dev_scaled,
    dtype=torch.float32,
    device=device
)


#-----------------------------
# tune with AAEO
#-----------------------------

# Search ranges for hyperparameters
# BOUNDS = {
#     "learning_rate": (1e-6, 5e-4),   
#     "weight_decay": (1e-6, 1e-3),
#     "dropout": (0.0, 0.2),
#     "epochs": (20, 80)           
# }

# # Randomly sample one candidate solution
# def random_individual():
#     return {
#         "learning_rate": float(np.random.uniform(*BOUNDS["learning_rate"])),
#         "weight_decay": float(np.random.uniform(*BOUNDS["weight_decay"])),
#         "dropout": float(np.random.uniform(*BOUNDS["dropout"])),
#         "epochs": int(np.random.randint(*BOUNDS["epochs"]))
#     }

# # -------------------------------------------------------
# # Evaluate one candidate hyperparameter configuration
# # Using 5-fold cross validation on real dataset
# # -------------------------------------------------------
# def evaluate(individual):

#     # Split real fine tuning data into 5 folds
#     # Ensures robust estimate of generalization performance
#     kf = KFold(n_splits=5, shuffle=True, random_state=42)
#     fold_scores = []

#     for train_idx, val_idx in kf.split(X_dev_scaled):
        
#         # ---------------------------------------------------
#         # Create training tensors for this fold
#         # ---------------------------------------------------
        
#         X_tr = torch.tensor(
#             X_dev_scaled[train_idx],
#             dtype=torch.float32,
#             device=device
#         )

#         y_tr = torch.tensor(
#             y_dev_scaled[train_idx],
#             dtype=torch.float32,
#             device=device
#         )

#         # ---------------------------------------------------
#         # Create validation tensors for this fold
#         # ---------------------------------------------------
#         X_va = torch.tensor(
#             X_dev_scaled[val_idx],
#             dtype=torch.float32,
#             device=device
#         )

#         y_va = torch.tensor(
#             y_dev_scaled[val_idx],
#             dtype=torch.float32,
#             device=device
#         )

#         # ---------------------------------------------------
#         # Rebuild transformer model with candidate dropout
#         # Architecture remains identical to synthetic training
#         # ---------------------------------------------------
#         model = FTTransformer(
#             num_numeric=len(numeric_cols),
#             d_model=int(saved_params["best_params"]["d_model"]),
#             n_layers=int(saved_params["best_params"]["n_layers"]),
#             dropout=float(individual["dropout"])
#         ).to(device)

        
#         # Load synthetic pretrained weights
#         # Start fine tuning from synthetic knowledge
#         model.load_state_dict(checkpoint["model_state_dict"], strict=False)

#         # ---------------------------------------------------
#         # Freeze transformer backbone
#         # Only regression head parameters will update
#         # Prevents catastrophic forgetting of synthetic patterns
#         # ---------------------------------------------------
#         for name, param in model.named_parameters():
#             if "head" not in name:
#                 param.requires_grad = False

#         # Confirm what is trainable
#         for name, param in model.named_parameters():
#             if param.requires_grad:
#                 print("Trainable:", name)

#         # ---------------------------------------------------
#         # Optimizer updates only trainable parameters (head)
#         # ---------------------------------------------------
#         optimizer = torch.optim.AdamW(
#         filter(lambda p: p.requires_grad, model.parameters()),
#         lr=float(individual["learning_rate"]),
#         weight_decay=float(individual["weight_decay"])
#         )

#         # Loss function for regression
#         criterion = torch.nn.MSELoss()

#         # ---------------------------------------------------
#         # Fine tuning loop
#         # Train only on fold training split
#         # ---------------------------------------------------
#         model.train()

#         for _ in range(int(individual["epochs"])):
#             optimizer.zero_grad()
#             preds = model(X_tr)
#             loss = criterion(preds, y_tr)
#             loss.backward()
#             optimizer.step()

#         # Validation
#         model.eval()
#         with torch.no_grad():
#             val_preds_scaled = model(X_va).cpu().numpy()

#         val_preds = target_scaler.inverse_transform(
#             val_preds_scaled.reshape(-1, 1)
#         ).flatten()

#         y_true = target_scaler.inverse_transform(
#             y_va.cpu().numpy().reshape(-1, 1)
#         ).flatten()

#         fold_scores.append(r2_score(y_true, val_preds))

#     return np.mean(fold_scores)

# # Small evolutionary optimization loop to tune CatBoost hyperparameters.
# # Find the combination of learning_rate, depth, l2_leaf_reg, and iterations that maximizes R2 on the validation set.

# # Create 8 candidate parameter sets per generation.
# POP_SIZE = 8

# #Take the current 8 parameter sets.
# #Slightly modify them.
# #Test the new ones.
# #Keep the better ones.
# GENERATIONS = 10

# # Randomly generate 8 different parameter sets from BOUNDS
# population = [random_individual() for _ in range(POP_SIZE)]

# # Train a model for each parameter set and compute its R2 on validation data. That R2 is the fitness score.
# fitness = [evaluate(ind) for ind in population]

# # Find which candidate performs best.
# best_idx = np.argmax(fitness)
# best_individual = population[best_idx]
# best_score = fitness[best_idx]

# print("Initial best R2:", best_score)

# for gen in range(GENERATIONS):
#     print(f"\nGeneration {gen + 1}")

#     # For each generation:
#     # Create new candidates
#     new_population = []
    
#     for i, ind in enumerate(population):

#         # For each current individual:
#         # With 50 percent probability:
#         if random.random() < 0.5:

#             # You combine it with another random candidate.
#             partner = population[np.random.randint(POP_SIZE)]

#             # new_value = current + random factor × difference from partner
#             # This is exploration using direction between two solutions.
#             new_ind = {
#                 k: ind[k] + np.random.uniform(-0.2, 0.2) * (partner[k] - ind[k])
#                 for k in ind
#             }
#         # Otherwise slightly perturb each parameter randomly.    
#         else:
#             new_ind = {
#                 k: ind[k] + np.random.uniform(-0.1, 0.1)
#                 for k in ind
#             }

#         # Force each parameter to remain within allowed limits using np.clip.
#         # This prevents invalid values.
#         new_ind["learning_rate"] = float(
#             np.clip(new_ind["learning_rate"], *BOUNDS["learning_rate"])
#         )

#         new_ind["weight_decay"] = float(
#             np.clip(new_ind["weight_decay"], *BOUNDS["weight_decay"])
#         )

#         new_ind["dropout"] = float(
#             np.clip(new_ind["dropout"], *BOUNDS["dropout"])
#         )

#         new_ind["epochs"] = int(
#             np.clip(new_ind["epochs"], *BOUNDS["epochs"])
#         )

#         new_population.append(new_ind)

#     # Train a model for each new parameter set and compute R2.
#     new_fitness = [evaluate(ind) for ind in new_population]

#     # Replace old population with new population if fitness improves.
#     for i in range(POP_SIZE):
#         if new_fitness[i] > fitness[i]:
#             population[i] = new_population[i]
#             fitness[i] = new_fitness[i]

#     # Track best performing candidate across all generations.
#     gen_best_idx = np.argmax(fitness)
#     if fitness[gen_best_idx] > best_score:
#         best_score = fitness[gen_best_idx]
#         best_individual = population[gen_best_idx]

#     print("Best R2 so far:", best_score)

#     # Save best parameters found
#     best_params = {
#         "learning_rate": float(best_individual["learning_rate"]),
#         "weight_decay": float(best_individual["weight_decay"]),
#         "dropout": float(best_individual["dropout"]),
#         "epochs": int(best_individual["epochs"])
#         }

# best_params_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/finetuned_best_params_AAEO.json"
# with open(best_params_path, "w") as f:
#     json.dump(best_params, f, indent=2)



# # -----------------------------
# # Train final fine tuned FTTransformer
# # -----------------------------

# best_params_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/finetuned_best_params_AAEO.json"

# with open(best_params_path, "r") as f:
#     best_params = json.load(f)

# # Rebuild transformer with same architecture as synthetic training
# # Only dropout changes according to tuned value
# model = FTTransformer(
#     num_numeric=len(numeric_cols),
#     d_model=int(saved_params["best_params"]["d_model"]),
#     n_layers=int(saved_params["best_params"]["n_layers"]),
#     dropout=float(best_params["dropout"])
# ).to(device)

# # Load synthetic pretrained weights
# # This initializes model with synthetic knowledge
# model.load_state_dict(checkpoint["model_state_dict"], strict=False)


# # Freeze transformer backbone
# # Only regression head parameters will be updated
# # This prevents catastrophic forgetting of synthetic patterns
# for name, param in model.named_parameters():
#     if "head" not in name:
#         param.requires_grad = False


# # Optimizer updates ONLY trainable parameters (the head)
# # learning_rate and weight_decay were tuned earlier
# optimizer = torch.optim.AdamW(
#     filter(lambda p: p.requires_grad, model.parameters()),
#     lr=float(best_params["learning_rate"]),
#     weight_decay=float(best_params["weight_decay"])
# )

# # Mean Squared Error for regression training
# criterion = torch.nn.MSELoss()

# # Switch model to training mode
# model.train()

# # Convert full real fine tuning dataset to tensors
# # Using scaled features and scaled target
# X_full = torch.tensor(
#     X_dev_scaled,
#     dtype=torch.float32,
#     device=device
# )

# y_full = torch.tensor(
#     y_dev_scaled,
#     dtype=torch.float32,
#     device=device
# )

# # Fine tuning loop on entire real training dataset
# # Only head weights update due to freezing
# best_loss = float("inf")
# patience = 10
# counter = 0

# for _ in range(int(best_params["epochs"])):

#     optimizer.zero_grad()
#     preds = model(X_full)
#     loss = criterion(preds, y_full)
#     loss.backward()
#     optimizer.step()

#     current_loss = loss.item()

#     if current_loss < best_loss:
#         best_loss = current_loss
#         counter = 0
#     else:
#         counter += 1

#     if counter >= patience:
#         break


# # Save fine tuned model
# torch.save({
#     "model_state_dict": model.state_dict(),
#     "numeric_cols": numeric_cols,
#     "target_scaler_mean": checkpoint["target_scaler_mean"],
#     "target_scaler_scale": checkpoint["target_scaler_scale"],
#     "feature_scaler_mean": checkpoint["feature_scaler_mean"],
#     "feature_scaler_scale": checkpoint["feature_scaler_scale"],
# }, "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_plus_real_fttransformer_model.pt")

# # -------------------------------------------
# # Load and run saved model on test data
# # -------------------------------------------

# #load model
checkpoint = torch.load(
    "modelB/models/ftTransformer/synthetic_plus_real_fttransformer_model.pt",
    #"/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_plus_real_fttransformer_model.pt",
    map_location=device
)

numeric_cols = checkpoint["numeric_cols"]

# Recreate model
model = FTTransformer(
num_numeric=len(numeric_cols),
d_model=int(saved_params["best_params"]["d_model"]),
n_layers=int(saved_params["best_params"]["n_layers"]),
dropout=float(best_params["dropout"])
).to(device)

model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

#restore scalers
feature_scaler = StandardScaler()
target_scaler = StandardScaler()

feature_scaler.mean_ = np.array(checkpoint["feature_scaler_mean"], dtype=float)
feature_scaler.scale_ = np.array(checkpoint["feature_scaler_scale"], dtype=float)

target_scaler.mean_ = np.array(checkpoint["target_scaler_mean"], dtype=float)
target_scaler.scale_ = np.array(checkpoint["target_scaler_scale"], dtype=float)

#load and preprocess data

#real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")


real_test = preprocess_real(real_test, require_target=True)

# Ensure numeric
real_test[numeric_cols] = real_test[numeric_cols].apply(
    pd.to_numeric
)

X_test = real_test[numeric_cols].values.astype(np.float32)
y_test = real_test["post_renovation_value"].values.astype(np.float32)

# Scale using training scaler
X_test_scaled = feature_scaler.transform(X_test)

X_test_t = torch.tensor(
    X_test_scaled,
    dtype=torch.float32,
    device=device
)

#predict
with torch.no_grad():
    preds_scaled = model(X_test_t).cpu().numpy()

preds = target_scaler.inverse_transform(
    preds_scaled.reshape(-1, 1)
).flatten()

r2 = r2_score(y_test, preds)
test_mape = mape(y_test, preds)

print("Loaded FTTransformer R2:", r2)
print("Loaded FTTransformer MAPE:", test_mape)

#save preds
preds_df = pd.DataFrame({
    "y_true": y_test,
    "y_pred": preds
})

preds_path = "modelB/ftTransformer/fttransformer_finetuned_synthetic_predictions.csv"
preds_df.to_csv(preds_path, index=False)
