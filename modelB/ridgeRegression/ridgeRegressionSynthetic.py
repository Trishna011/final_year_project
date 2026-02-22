import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
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

def preprocess_real_data(df):
    df = df.copy()

    # --------------------------------------------------
    # 1. Fix column names
    # --------------------------------------------------
    
    df["structural_change"] = df["structural_changes"]

    # --------------------------------------------------
    # 2. Encode material_grade to numeric
    # MUST match synthetic encoding if used during training
    # Adjust mapping if different
    # --------------------------------------------------
    material_map = {
        "mid-range": 1,
        "high-end": 2,
        "low-end": 0
    }

    df["material_grade"] = df["material_grade"].map(material_map).fillna(1)

    # --------------------------------------------------
    # 4. Create renovation flags from type_of_renovation
    # --------------------------------------------------
    def parse_flags(val):
        flags = {
            "reno_bathroom": 0,
            "reno_bedroom": 0,
            "reno_kitchen": 0,
            "reno_living_room": 0,
            "reno_other_custom": 0,
            "reno_full_renovation": 0
        }

        if pd.isna(val) or val == "":
            return flags

        if isinstance(val, str):
            try:
                parsed = eval(val)
            except:
                parsed = []
        else:
            parsed = val

        if not isinstance(parsed, list):
            return flags

        for room in parsed:
            r = str(room).lower()
            if "bathroom" in r:
                flags["reno_bathroom"] = 1
            elif "bedroom" in r:
                flags["reno_bedroom"] = 1
            elif "kitchen" in r:
                flags["reno_kitchen"] = 1
            elif "living" in r:
                flags["reno_living_room"] = 1
            elif "other" in r:
                flags["reno_other_custom"] = 1

        return flags

    flag_df = df["type_of_renovation"].apply(parse_flags).apply(pd.Series)
    df = pd.concat([df, flag_df], axis=1)

    # --------------------------------------------------
    # 5. Ensure numeric types
    # --------------------------------------------------
    numeric_cols = [
        "property_size",
        "renovation_cost",
        "sqft_renovated",
        "sqft_to_add",
        "structural_change"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --------------------------------------------------
    # 6. Select exact feature order
    # --------------------------------------------------
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

    return df[features]

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

# test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")

# # Drop missing targets
# test_exp = test_exp.dropna(subset=[target])

# # Ensure correct feature order
# X_test = test_exp[features].copy()
# y_test = test_exp[target]

# test_preds = ridge_pipeline.predict(X_test)

# # build prediction dataframe
# pred_df = pd.DataFrame({
#     "source_row": test_exp["source_row"].values,
#     "y_true": y_test.values,
#     "y_pred": test_preds
# })

# # aggregate to property level
# prop_level = pred_df.groupby("source_row", as_index=False).agg(
#     y_true=("y_true", "first"),
#     y_pred=("y_pred", "mean")
# )

# # metrics
# r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
# val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

# print("Ridge Regression R2 (synthetic):", r2)
# print("Ridge Regression MAPE (synthetic):", val_mape)


# -----------------------
# Preds real data
# -----------------------
real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# Ground truth (post renovation value)
y_true = real_df["price"].astype(float)

# Preprocess features
real_df_processed = preprocess_real_data(real_df)

# Ensure feature alignment
real_X = real_df_processed[features]

real_preds = ridge_pipeline.predict(real_X)

r2 = r2_score(y_true, real_preds)
real_mape = mape(y_true, real_preds)

print("Real Data R2:", r2)
print("Real Data MAPE:", real_mape)

# -------------------------------------------------------
# Save predictions for Wilcoxon test 
# -------------------------------------------------------
ridge_preds_path = "modelB/ridgeRegression/ridge_train_real_preds.csv"

pred_df = pd.DataFrame({
    "source_row": real_df.index,
    "y_true": y_true.values,
    "y_pred": real_preds
})

# pred_df = pd.DataFrame({
#     "source_row": prop_level["y_true"].index,
#     "y_true": prop_level["y_true"].values,
#     "y_pred": prop_level["y_pred"].values
# })

pred_df.to_csv(ridge_preds_path, index=False)

