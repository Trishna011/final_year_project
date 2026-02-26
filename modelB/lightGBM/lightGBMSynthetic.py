import json
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import numpy as np
from sklearn.model_selection import ParameterGrid
import pandas as pd
from lightgbm import LGBMRegressor, early_stopping, LGBMRegressor
import joblib

# -------------------------------------------------------
# Load expanded synthetic training and validation data
# -------------------------------------------------------
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")
test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")

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

# -------------------------------------------------------
# Define target and feature columns
# Target is synthetic post renovation value
# -------------------------------------------------------
for df in [train_exp, val_exp, test_exp]:
    if "unit_type" in df.columns:
        df.drop(columns=["unit_type"], inplace=True)

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

# Remove rows where target is missing
train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])
test_exp = test_exp.dropna(subset=[target])

# Split features and target
X_train = train_exp[features]

y_train = train_exp[target]

X_val = val_exp[features]

y_val = val_exp[target]

X_test = test_exp[features]
y_test = test_exp[target]


# -------------------------------------------------------
# Hyperparameter grid
# -------------------------------------------------------
# param_grid = {
#     "num_leaves": [31, 63],
#     "learning_rate": [0.03, 0.05],
#     "n_estimators": [1500, 2000],
#     "subsample": [0.8],
#     "colsample_bytree": [0.8]
# }

# best_r2 = -np.inf
# best_params = None
# best_model = None

# # -------------------------------------------------------
# # Grid search
# # -------------------------------------------------------
# for params in ParameterGrid(param_grid):

#     # Create model with current parameters
#     model = LGBMRegressor(
#         objective="regression",
#         random_state=42,
#         **params
#     )

#     # Train model
#     model.fit(
#         X_train,
#         y_train,
#         eval_set=[(X_val, y_val)],
#         eval_metric="rmse",
#         callbacks=[early_stopping(100, verbose=False)]
#     )

#     # Predict on validation set
#     val_preds = model.predict(X_val)

#     # Combine predictions with real values
#     pred_df = pd.DataFrame({
#         "source_row": val_exp["source_row"].values,
#         "y_true": y_val.values,
#         "y_pred": val_preds,
#     })
    
#     # Average predictions per property
#     prop_level = pred_df.groupby("source_row", as_index=False).agg(
#         y_true=("y_true", "first"),
#         y_pred=("y_pred", "mean"),
#     )

#     # Calculate R2 and MAPE
#     r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
#     val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

#      # Keep best model based on R2
#     if r2 > best_r2:
#         best_r2 = r2
#         best_params = params
#         best_model = model

#     print("tested:", params, "R2:", r2, "MAPE:", val_mape)

# print("best R2:", best_r2)
# print("best params:", best_params)

# # -------------------------------------------------------
# # Save best parameters
# # -------------------------------------------------------
# params_path = "modelB/models/lightGBM/lightgbm_synthetic_best_params.json"

# params_to_save = {
#     "model_params": best_params,
#     "feature_columns": list(X_train.columns)
# }

# with open(params_path, "w") as f:
#     json.dump(params_to_save, f, indent=2)

# # -------------------------------------------------------
# # Save best model
# # -------------------------------------------------------
# joblib.dump(best_model, "modelB/models/lightGBM/lightgbm_synthetic_model.pkl")

# # -------------------------------------------------------
# # Final preds on test set
# # -------------------------------------------------------
best_model = joblib.load("modelB/models/lightGBM/lightgbm_synthetic_model.pkl")
test_preds = best_model.predict(X_test)

pred_df = pd.DataFrame({
    "source_row": test_exp["source_row"].values,
    "y_true": y_test.values,
    "y_pred": test_preds,
})

# Average predictions per property
prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean"),
)

# Evaluate performance
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
test_mape = mape(prop_level["y_true"], prop_level["y_pred"])
rmse = np.sqrt(mean_squared_error(prop_level["y_true"], prop_level["y_pred"]))
mae = mean_absolute_error(prop_level["y_true"], prop_level["y_pred"])

print("Test R2:", r2)
print("Test MAPE:", test_mape)
print("Test RMSE:", rmse)
print("Test MAE:", mae)

# -------------------------------------------------------
# Final preds on real data test set
# -------------------------------------------------------

# model = joblib.load("modelB/models/lightGBM/lightgbm_synthetic_model.pkl")
# print("Model expects features:", model.booster_.num_feature())

# real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# # Preprocess features
# real_df_processed = preprocess_real(real_test)

# # Ground truth (post renovation value)
# y_true = real_df_processed["price"].astype(float)

# # Ensure feature alignment
# real_X = real_df_processed[features]

# real_preds = model.predict(real_X)

# r2 = r2_score(y_true, real_preds)
# real_mape = mape(y_true, real_preds)
# rmse = np.sqrt(mean_squared_error(y_true, real_preds))
# mae = mean_absolute_error(y_true, real_preds)

# print("Real Data R2:", r2)
# print("Real Data MAPE:", real_mape)
# print("Real Data RMSE:", rmse)
# print("Real Data MAE:", mae)

# -------------------------------------------------------
# Save predictions for Wilcoxon test 
# -------------------------------------------------------
# catboost_preds_path = "modelB/lightGBM/lightgbm_train_real_preds.csv"

# pred_df = pd.DataFrame({
#     "source_row": real_df_processed.index,
#     "y_true": y_true.values,
#     "y_pred": real_preds
# })

# pred_df.to_csv(catboost_preds_path, index=False)

# print(f"Saved CatBoost synthetic predictions to {catboost_preds_path}")
