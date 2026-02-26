import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import json
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

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

# load synthetic data
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")

target = "post_renovation_value"

features = [
    "property_size",
    "location",
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
    "reno_full_renovation"
]

# drop missing targets
train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])

X_train = train_exp[features]
y_train = train_exp[target]

X_val = val_exp[features]
y_val = val_exp[target]

# ============================
# PIPELINE WITH SCALING
# ============================

# ridge_pipeline = Pipeline([
#     ("scaler", StandardScaler()),
#     ("ridge", Ridge(alpha=1.0))
# ])

# ridge_pipeline.fit(X_train, y_train)

# # -------------------------
# # Save model
# # -------------------------
# model_path = "modelB/models/ridgeRegression/ridge_synthetic_model.pkl"
# joblib.dump(ridge_pipeline, model_path)

# print("Saved ridge regression model to:", model_path)

# # -------------------------
# # SAVE PARAMETERS + FEATURE COLUMNS
# # -------------------------

# params_path = "modelB/models/ridgeRegression/ridge_synthetic_best_params.json"

# params_to_save = {
#     "ridge_params": ridge_pipeline.named_steps["ridge"].get_params(),
#     "feature_columns": list(X_train.columns)
# }

# with open(params_path, "w") as f:
#     json.dump(params_to_save, f, indent=2)

# ----------------------
# Load models and features
# ----------------------
# Load model
model_path = "modelB/models/ridgeRegression/ridge_synthetic_model.pkl"
ridge_pipeline = joblib.load(model_path)

# Load feature column order
params_path = "modelB/models/ridgeRegression/ridge_synthetic_best_params.json"
with open(params_path, "r") as f:
    saved = json.load(f)

features = saved["feature_columns"]
target = "post_renovation_value"

# --------------------
# Predictions SYNTEHTIC TEST
# --------------------

test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")

# Drop missing targets
test_exp = test_exp.dropna(subset=[target])

# Ensure correct feature order
X_test = test_exp[features].copy()
y_test = test_exp[target]

test_preds = ridge_pipeline.predict(X_test)

# build prediction dataframe
pred_df = pd.DataFrame({
    "source_row": test_exp["source_row"].values,
    "y_true": y_test.values,
    "y_pred": test_preds
})

# aggregate to property level
prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# metrics
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])
rmse = np.sqrt(mean_squared_error(prop_level["y_true"], prop_level["y_pred"]))
mae = mean_absolute_error(prop_level["y_true"], prop_level["y_pred"])

print("Ridge Regression R2 (synthetic):", r2)
print("Ridge Regression MAPE (synthetic):", val_mape)
print("Ridge Regression RMSE (synthetic):", rmse)
print("Ridge Regression MAE (synthetic):", mae)


# -----------------------
# Preds real data
# -----------------------
# real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# real_df = preprocess_real(real_df)

# y_true = real_df["price"]

# X_real = real_df[features]

# real_preds = ridge_pipeline.predict(X_real)

# real_r2 = r2_score(y_true, real_preds)
# real_mape = mape(y_true, real_preds)
# rmse = np.sqrt(mean_squared_error(y_true, real_preds))
# mae = mean_absolute_error(y_true, real_preds)

# print("Random Forest R2 (real test):", real_r2)
# print("Random Forest MAPE (real test):", real_mape)
# print("Random Forest RMSE (real test):", rmse)
# print("Random Forest MAE (real test):", mae)

# -------------------------------------------------------
# Save predictions for Wilcoxon test 
# -------------------------------------------------------
# ridge_preds_path = "modelB/ridgeRegression/ridge_train_real_preds.csv"

# pred_df = pd.DataFrame({
#     "source_row": real_df.index,
#     "y_true": y_true.values,
#     "y_pred": real_preds
# })

# pred_df = pd.DataFrame({
#     "source_row": prop_level["y_true"].index,
#     "y_true": prop_level["y_true"].values,
#     "y_pred": prop_level["y_pred"].values
# })

# pred_df.to_csv(ridge_preds_path, index=False)

