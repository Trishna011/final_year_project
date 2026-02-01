import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
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
# IMPUTE + SCALE
# =========================

imputer = SimpleImputer(strategy="median")
scaler = StandardScaler()

X_train_imp = imputer.fit_transform(X_train_enc)
X_val_imp = imputer.transform(X_val_enc)

X_train_scaled = scaler.fit_transform(X_train_imp)
X_val_scaled = scaler.transform(X_val_imp)

# =========================
# TRAIN SVR
# =========================

svr_model = SVR(
    kernel="rbf",
    C=100,
    epsilon=0.1,
    gamma="scale"
)

svr_model.fit(X_train_scaled, y_train)

# =========================
# PREDICT
# =========================

val_preds = svr_model.predict(X_val_scaled)

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
