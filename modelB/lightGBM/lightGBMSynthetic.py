import numpy as np
import pandas as pd
import json
from lightgbm import LGBMRegressor, early_stopping, log_evaluation
from sklearn.metrics import r2_score

# =========================
# LOAD DATA
# =========================

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

train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])

X_train = train_exp[features]
y_train = train_exp[target]

X_val = val_exp[features]
y_val = val_exp[target]

# =========================
# ONE HOT ENCODE
# =========================

X_train_enc = pd.get_dummies(X_train, drop_first=True)
X_val_enc = pd.get_dummies(X_val, drop_first=True)

X_val_enc = X_val_enc.reindex(columns=X_train_enc.columns, fill_value=0)

# =========================
# TRAIN LIGHTGBM
# =========================

model = LGBMRegressor(
    n_estimators=2000,
    learning_rate=0.05,
    max_depth=-1,
    num_leaves=31,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(
    X_train_enc,
    y_train,
    eval_set=[(X_val_enc, y_val)],
    eval_metric="l1",
    callbacks=[
        early_stopping(stopping_rounds=100),
        log_evaluation(period=0)
    ]
)

#=========================
# SAVE MODEL
#=========================

model_path = "modelB/models/lightGBM/lightgbm_synthetic_model.txt"
model.booster_.save_model(model_path)

print(f"Saved LightGBM synthetic model to {model_path}")

# =========================
# SAVE PARAMETERS + FEATURE COLUMNS
# =========================

params_path = "modelB/models/lightGBM/lightgbm_synthetic_best_params.json"

params_to_save = {
    "model_params": model.get_params(),
    "feature_columns": list(X_train_enc.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)

# =========================
# PREDICT
# =========================

val_preds = model.predict(X_val_enc)

# =========================
# PROPERTY LEVEL AGGREGATION
# =========================

pred_df = pd.DataFrame({
    "source_row": val_exp["source_row"].values,
    "y_true": y_val.values,
    "y_pred": val_preds
})

prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# =========================
# METRICS
# =========================

def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("LightGBM R2 (synthetic):", r2)
print("LightGBM MAPE (synthetic):", val_mape)

# =========================
# SAVE PREDICTIONS FOR WILCOXON
# =========================

lightgbm_preds_path = "modelB/lightGBM/lightgbm_synthetic_preds.csv"

prop_level.to_csv(lightgbm_preds_path, index=False)

print(f"Saved LightGBM synthetic predictions to {lightgbm_preds_path}")
