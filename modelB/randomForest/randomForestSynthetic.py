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
    "unit_type",
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

# one hot encode categoricals
X_train_enc = pd.get_dummies(X_train, drop_first=True)
X_val_enc = pd.get_dummies(X_val, drop_first=True)

# align columns
X_val_enc = X_val_enc.reindex(columns=X_train_enc.columns, fill_value=0)

# train Random Forest
rf_model = RandomForestRegressor(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train_enc, y_train)

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
    "feature_columns": list(X_train_enc.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)


# predict
val_preds = rf_model.predict(X_val_enc)

# aggregate to property level
pred_df = pd.DataFrame({
    "source_row": val_exp["source_row"].values,
    "y_true": y_val.values,
    "y_pred": val_preds
})

prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# metrics
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("Random Forest R2 (synthetic):", r2)
print("Random Forest MAPE (synthetic):", val_mape)

# save predictions for Wilcoxon test
rf_preds_path = "modelB/randomForest/randomforest_synthetic_preds.csv"

rf_preds_df = pd.DataFrame({
    "source_row": prop_level.index,
    "y_true": prop_level["y_true"].values,
    "y_pred": prop_level["y_pred"].values
})

rf_preds_df.to_csv(rf_preds_path, index=False)

print(f"Saved Random Forest synthetic predictions to {rf_preds_path}")
