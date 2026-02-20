import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score
import joblib
import json
from sklearn.model_selection import ParameterGrid, KFold, GridSearchCV
from sklearn.pipeline import Pipeline


# =========================
# LOAD DATA
# =========================

train_exp = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_train_expanded.csv")
val_exp = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_val_expanded.csv")
test_exp = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_test_expanded.csv")


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
"svr__C": [10, 100],
"svr__epsilon": [0.01, 0.1],
"svr__gamma": ["scale", 0.01]
}

best_r2 = -np.inf
best_params = None
best_model = None

kf = KFold(n_splits=5, shuffle=True, random_state=42)

grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring="r2",
    n_jobs=8
)

grid.fit(X_train_enc, y_train)


print("Best CV R2:", grid.best_score_)
print("Best params:", grid.best_params_)

best_model = grid.best_estimator_


model_bundle = {
"model": best_model
}

#model_path = "modelB/models/SVR/svr_synthetic_model.pkl"
model_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_model.pkl"
joblib.dump(model_bundle, model_path)


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

#model_path = "modelB/models/SVR/svr_synthetic_model.pkl"
model_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_model.pkl"
joblib.dump(model_bundle, model_path)
# -------------------------
# SAVE PARAMETERS + FEATURE COLUMNS
# -------------------------

#params_path = "modelB/models/SVR/svr_synthetic_best_params.json"
params_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_best_params.json"

params_to_save = {
"best_params": grid.best_params_,
"feature_columns": list(X_train_enc.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)

raw_r2 = r2_score(y_val, val_preds)
print("Row-level R2:", raw_r2)
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
# Test on test set
# =========================

test_exp = test_exp.dropna(subset=[target])

X_test = test_exp[features]
y_test = test_exp[target]

X_test_enc = pd.get_dummies(X_test, drop_first=True)
X_test_enc = X_test_enc.reindex(columns=X_train_enc.columns, fill_value=0)

test_preds = best_model.predict(X_test_enc)

test_df = pd.DataFrame({
"source_row": test_exp["source_row"].values,
"y_true": y_test.values,
"y_pred": test_preds
})

test_prop_level = test_df.groupby("source_row", as_index=False).agg(
y_true=("y_true", "first"),
y_pred=("y_pred", "mean")
)

test_r2 = r2_score(test_prop_level["y_true"], test_prop_level["y_pred"])
test_mape = mape(test_prop_level["y_true"], test_prop_level["y_pred"])

print("SVR TEST R2 (synthetic):", test_r2)
print("SVR TEST MAPE (synthetic):", test_mape)

test_preds_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_test_preds.csv"
test_prop_level.to_csv(test_preds_path, index=False)
print(f"Saved SVR synthetic TEST predictions to {test_preds_path}")

# =========================
# SAVE PREDICTIONS FOR WILCOXON
# =========================

#svr_preds_path = "modelB/svr/svr_synthetic_preds.csv"
svr_preds_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_preds.csv"

prop_level.to_csv(svr_preds_path, index=False)

print(f"Saved SVR synthetic predictions to {svr_preds_path}")
