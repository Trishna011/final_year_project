import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import json


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

# test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")
# test_exp = test_exp.dropna(subset=[target])

# X_test = test_exp[features]
# y_test = test_exp[target]

# # Predict
# test_preds = rf_model.predict(X_test)

# # Aggregate to property level
# pred_df = pd.DataFrame({
#     "source_row": test_exp["source_row"].values,
#     "y_true": y_test.values,
#     "y_pred": test_preds
# })

# prop_level = pred_df.groupby("source_row", as_index=False).agg(
#     y_true=("y_true", "first"),
#     y_pred=("y_pred", "mean")
# )

# # Metrics
# test_r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
# test_mape = mape(prop_level["y_true"], prop_level["y_pred"])

# print("Random Forest R2 (synthetic test):", test_r2)
# print("Random Forest MAPE (synthetic test):", test_mape)

# -----------------------------------
# Evaluate on real test set
# -----------------------------------
model_path = "modelB/models/randomForest/randomforest_synthetic_model.pkl"
rf_model = joblib.load(model_path)

real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

y_true = real_df["price"]

real_df = preprocess_real_data(real_df)

# Ensure missing columns are added
for col in features:
    if col not in real_df.columns:
        real_df[col] = 0

X_real = real_df[features]

real_preds = rf_model.predict(X_real)

real_r2 = r2_score(y_true, real_preds)
real_mape = mape(y_true, real_preds)

print("Random Forest R2 (real test):", real_r2)
print("Random Forest MAPE (real test):", real_mape)

#----------------------------------
# save predictions for Wilcoxon test
#----------------------------------
rf_preds_path = "modelB/randomForest/randomforest_train_real_preds.csv"

pred_df = pd.DataFrame({
    "source_row": real_df.index,
    "y_true": y_true.values,
    "y_pred": real_preds
})

pred_df.to_csv(rf_preds_path, index=False)

print(f"Saved Random Forest synthetic predictions to {rf_preds_path}")
