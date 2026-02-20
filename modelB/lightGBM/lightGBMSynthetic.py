import json
from sklearn.metrics import r2_score
import numpy as np
from sklearn.model_selection import ParameterGrid
import pandas as pd
from lightgbm import LGBMRegressor, early_stopping

# -------------------------------------------------------
# Load expanded synthetic training and validation data
# -------------------------------------------------------
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")

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
    # 3. Create unit_type default
    # --------------------------------------------------
    df["unit_type"] = "house"

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
        "unit_type",
        "reno_bathroom",
        "reno_bedroom",
        "reno_kitchen",
        "reno_living_room",
        "reno_other_custom",
        "reno_full_renovation"
        ]

    return df[features]

# -------------------------------------------------------
# Define target and feature columns
# Target is synthetic post renovation value
# -------------------------------------------------------
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

# Remove rows where target is missing
train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])

# Split features and target
X_train = train_exp[features]
y_train = train_exp[target]

X_val = val_exp[features]
y_val = val_exp[target]

# -------------------------------------------------------
# Convert categorical columns to category dtype
# -------------------------------------------------------
categorical_cols = ["unit_type"]

for col in categorical_cols:
    X_train[col] = X_train[col].astype("category")
    X_val[col] = X_val[col].astype("category")


# -------------------------------------------------------
# Hyperparameter grid
# -------------------------------------------------------
param_grid = {
    "num_leaves": [31, 63],
    "learning_rate": [0.03, 0.05],
    "n_estimators": [1500, 2000],
    "subsample": [0.8],
    "colsample_bytree": [0.8]
}

best_r2 = -np.inf
best_params = None
best_model = None

# -------------------------------------------------------
# Grid search
# -------------------------------------------------------
for params in ParameterGrid(param_grid):

    model = LGBMRegressor(
        objective="regression",
        random_state=42,
        **params
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="rmse",
        callbacks=[early_stopping(100, verbose=False)]
    )

    val_preds = model.predict(X_val)

    pred_df = pd.DataFrame({
        "source_row": val_exp["source_row"].values,
        "y_true": y_val.values,
        "y_pred": val_preds,
    })

    prop_level = pred_df.groupby("source_row", as_index=False).agg(
        y_true=("y_true", "first"),
        y_pred=("y_pred", "mean"),
    )

    r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
    val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

    if r2 > best_r2:
        best_r2 = r2
        best_params = params
        best_model = model

    print("tested:", params, "R2:", r2, "MAPE:", val_mape)

print("best R2:", best_r2)
print("best params:", best_params)

# -------------------------------------------------------
# Save best parameters
# -------------------------------------------------------
params_path = "modelB/models/lightGBM/lightgbm_synthetic_best_params.json"

params_to_save = {
    "model_params": best_params,
    "feature_columns": list(X_train.columns)
}

with open(params_path, "w") as f:
    json.dump(params_to_save, f, indent=2)

# -------------------------------------------------------
# Save best model
# -------------------------------------------------------
model_path = "modelB/models/lightGBM/lightgbm_synthetic_best_model.txt"
best_model.booster_.save_model(model_path)

print("saved model to:", model_path)

# -------------------------------------------------------
# Final validation predictions
# -------------------------------------------------------
val_preds = best_model.predict(X_val)

pred_df = pd.DataFrame({
    "source_row": val_exp["source_row"].values,
    "y_true": y_val.values,
    "y_pred": val_preds,
})

prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean"),
)

r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("final R2 with best params:", r2)
print("final MAPE with best params:", val_mape)

# -------------------------------------------------------
# Save predictions for Wilcoxon test
# -------------------------------------------------------
lightgbm_preds_path = "modelB/lightGBM/lightgbm_synthetic_preds.csv"
prop_level.to_csv(lightgbm_preds_path, index=False)

print("Saved LightGBM synthetic predictions to", lightgbm_preds_path)
