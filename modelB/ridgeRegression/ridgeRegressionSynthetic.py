import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
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

# ------------------------
# train ridge regression
# ------------------------

ridge_model = Ridge(alpha=1.0)
ridge_model.fit(X_train_enc, y_train)


# -------------------------
# Save model
# -------------------------
model_path = "modelB/models/ridgeRegression/ridge_synthetic_model.pkl"
joblib.dump(ridge_model, model_path)

print("Saved ridge regression model to:", model_path)

# -------------------------
# SAVE PARAMETERS + FEATURE COLUMNS
# -------------------------

params_path = "modelB/models/ridgeRegression/ridge_synthetic_best_params.json"

params_to_save = {
    "model_params": ridge_model.get_params(),
    "feature_columns": list(X_train_enc.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)


# predict
val_preds = ridge_model.predict(X_val_enc)

# build prediction dataframe
pred_df = pd.DataFrame({
    "source_row": val_exp["source_row"].values,
    "y_true": y_val.values,
    "y_pred": val_preds
})

# aggregate to property level
prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# save predictions for Wilcoxon test
ridge_preds_path = "modelB/ridgeRegression/ridge_synthetic_preds.csv"

prop_level_out = prop_level.copy()
prop_level_out = prop_level_out.rename(columns={
    "y_true": "y_true",
    "y_pred": "y_pred"
})

prop_level_out.to_csv(ridge_preds_path, index=False)

print(f"Saved Ridge synthetic predictions to {ridge_preds_path}")

# MAPE function
def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

# metrics
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("Ridge Regression R2 (synthetic):", r2)
print("Ridge Regression MAPE (synthetic):", val_mape)
