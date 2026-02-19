import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score
import joblib
import json
from sklearn.model_selection import ParameterGrid, KFold
from sklearn.pipeline import Pipeline


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

# =========================================
# BUILD PIPELINE
# =========================================

pipeline = Pipeline([
("imputer", SimpleImputer(strategy="median")),
("scaler", StandardScaler()),
("svr", SVR(kernel="rbf"))
])

# =========================================
# PARAMETER GRID
# =========================================

param_grid = {
"svr__C": [1, 10, 50, 100, 300],
"svr__epsilon": [0.01, 0.1, 1],
"svr__gamma": ["scale", 0.001, 0.01, 0.05]
}

best_r2 = -np.inf
best_params = None
best_model = None

kf = KFold(n_splits=5, shuffle=True, random_state=42)

for params in ParameterGrid(param_grid):

    pipeline.set_params(**params)

    fold_scores = []

    for train_idx, val_idx in kf.split(X_train_enc):

        X_tr = X_train_enc.iloc[train_idx]
        y_tr = y_train.iloc[train_idx]

        X_va = X_train_enc.iloc[val_idx]
        y_va = y_train.iloc[val_idx]

        pipeline.fit(X_tr, y_tr)
        preds = pipeline.predict(X_va)

        fold_scores.append(r2_score(y_va, preds))

    mean_r2 = np.mean(fold_scores)

    print("tested:", params, "R2:", mean_r2)

    if mean_r2 > best_r2:
        best_r2 = mean_r2
        best_params = params
        best_model = joblib.dump(pipeline)


print("\nBest R2:", best_r2)
print("Best params:", best_params)

best_model.fit(X_train_enc, y_train)


val_preds = best_model.predict(X_val_enc)

pred_df = pd.DataFrame({
"source_row": val_exp["source_row"].values,
"y_true": y_val.values,
"y_pred": val_preds
})

prop_level = pred_df.groupby("source_row", as_index=False).agg(
y_true=("y_true", "first"),
y_pred=("y_pred", "mean")
)

r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
print("Final R2:", r2)
# -------------------------
# Save model
# -------------------------
model_bundle = {
"model": best_model,
}

model_path = "modelB/models/SVR/svr_synthetic_model.pkl"
joblib.dump(model_bundle, model_path)
# -------------------------
# SAVE PARAMETERS + FEATURE COLUMNS
# -------------------------

params_path = "modelB/models/SVR/ridge_synthetic_best_params.json"

params_to_save = {
    "model_params": best_model.get_params(),
    "feature_columns": list(X_train_enc.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)


# =========================
# AGGREGATE TO PROPERTY LEVEL
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
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("SVR R2 (synthetic):", r2)
print("SVR MAPE (synthetic):", val_mape)

# =========================
# SAVE PREDICTIONS FOR WILCOXON
# =========================

svr_preds_path = "modelB/svr/svr_synthetic_preds.csv"

prop_level.to_csv(svr_preds_path, index=False)

print(f"Saved SVR synthetic predictions to {svr_preds_path}")
