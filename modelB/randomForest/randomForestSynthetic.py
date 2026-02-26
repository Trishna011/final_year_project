import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import json


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


# train Random Forest
rf_model = RandomForestRegressor(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)

# -------------------------
# Save model
# -------------------------
model_path = "modelB/models/randomForest/randomforest_synthetic_model.pkl"
joblib.dump(rf_model, model_path)

print("Saved Random Forest model to:", model_path)

# -------------------------
# SAVE PARAMETERS + FEATURE COLUMNS
# -------------------------

params_path = "modelB/models/randomForest/randomforest_synthetic_best_params.json"

params_to_save = {
    "model_params": rf_model.get_params(),
    "feature_columns": list(X_train.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)

# -----------------------------------
# Evaluate on synthetic test set
# -----------------------------------

test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")
test_exp = test_exp.dropna(subset=[target])

X_test = test_exp[features]
y_test = test_exp[target]

# Predict
test_preds = rf_model.predict(X_test)

# Aggregate to property level
pred_df = pd.DataFrame({
    "source_row": test_exp["source_row"].values,
    "y_true": y_test.values,
    "y_pred": test_preds
})

prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# Metrics
test_r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
test_mape = mape(prop_level["y_true"], prop_level["y_pred"])
rmse = np.sqrt(mean_squared_error(prop_level["y_true"], prop_level["y_pred"]))
mae = mean_absolute_error(prop_level["y_true"], prop_level["y_pred"])

print("Random Forest R2 (synthetic test):", test_r2)
print("Random Forest MAPE (synthetic test):", test_mape)
print("Random Forest RMSE (synthetic test):", rmse)
print("Random Forest MAE (synthetic test):", mae)

# -----------------------------------
# Evaluate on real test set
# -----------------------------------
# model_path = "modelB/models/randomForest/randomforest_synthetic_model.pkl"
# rf_model = joblib.load(model_path)

# real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# real_df = preprocess_real(real_df)

# y_true = real_df["price"]

# X_real = real_df[features]

# real_preds = rf_model.predict(X_real)

# real_r2 = r2_score(y_true, real_preds)
# real_mape = mape(y_true, real_preds)
# rmse = np.sqrt(mean_squared_error(y_true, real_preds))
# mae = mean_absolute_error(y_true, real_preds)

# print("Random Forest R2 (real test):", real_r2)
# print("Random Forest MAPE (real test):", real_mape)
# print("Random Forest RMSE (real test):", rmse)
# print("Random Forest MAE (real test):", mae)

#----------------------------------
# save predictions for Wilcoxon test
#----------------------------------
# rf_preds_path = "modelB/randomForest/randomforest_train_real_preds.csv"

# pred_df = pd.DataFrame({
#     "source_row": real_df.index,
#     "y_true": y_true.values,
#     "y_pred": real_preds
# })

# pred_df.to_csv(rf_preds_path, index=False)

# print(f"Saved Random Forest synthetic predictions to {rf_preds_path}")
