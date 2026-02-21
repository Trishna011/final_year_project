import json
from sklearn.metrics import r2_score
import numpy as np
from sklearn.model_selection import ParameterGrid
import pandas as pd
from lightgbm import LGBMRegressor, early_stopping, LGBMRegressor
import joblib

# -------------------------------------------------------
# Load expanded synthetic training and validation data
# -------------------------------------------------------
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")
test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")

# -------------------------------------------------------
# Define MAPE metric
# -------------------------------------------------------
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

# -------------------------------------------------------
# Define target and feature columns
# Target is synthetic post renovation value
# -------------------------------------------------------
for df in [train_exp, val_exp, test_exp]:
    if "unit_type" in df.columns:
        df.drop(columns=["unit_type"], inplace=True)

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

# Remove rows where target is missing
train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])
test_exp = test_exp.dropna(subset=[target])

# Split features and target
X_train = train_exp[features]

y_train = train_exp[target]

X_val = val_exp[features]

y_val = val_exp[target]

X_test = test_exp[features]
y_test = test_exp[target]


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

    # Create model with current parameters
    model = LGBMRegressor(
        objective="regression",
        random_state=42,
        **params
    )

    # Train model
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="rmse",
        callbacks=[early_stopping(100, verbose=False)]
    )

    # Predict on validation set
    val_preds = model.predict(X_val)

    # Combine predictions with real values
    pred_df = pd.DataFrame({
        "source_row": val_exp["source_row"].values,
        "y_true": y_val.values,
        "y_pred": val_preds,
    })
    
    # Average predictions per property
    prop_level = pred_df.groupby("source_row", as_index=False).agg(
        y_true=("y_true", "first"),
        y_pred=("y_pred", "mean"),
    )

    # Calculate R2 and MAPE
    r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
    val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

     # Keep best model based on R2
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
joblib.dump(best_model, "modelB/models/lightGBM/lightgbm_synthetic_model.pkl")

# -------------------------------------------------------
# Final preds on test set
# -------------------------------------------------------

test_preds = best_model.predict(X_test)

pred_df = pd.DataFrame({
    "source_row": test_exp["source_row"].values,
    "y_true": y_test.values,
    "y_pred": test_preds,
})

# Average predictions per property
prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean"),
)

# Evaluate performance
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
test_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("Test R2:", r2)
print("Test MAPE:", test_mape)

# -------------------------------------------------------
# Final preds on real data test set
# -------------------------------------------------------

model = joblib.load("modelB/models/lightGBM/lightgbm_synthetic_model.pkl")
print("Model expects features:", model.booster_.num_feature())

real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# True values
y_true = real_test["price"].astype(float).values

# Preprocess
X_real = preprocess_real_data(real_test).copy()

# Ensure same column order
X_real = X_real[features]


# Predict
preds = model.predict(X_real)

# Attach predictions
real_test["predicted_post_renovation_value"] = preds

# Evaluate
r2 = r2_score(y_true, preds)

mask = y_true != 0
mape_val = np.mean(np.abs((y_true[mask] - preds[mask]) / y_true[mask])) * 100

print("Real R2:", r2)
print("Real MAPE:", mape_val)

# Save
real_test.to_csv("modelB/lightGBM/lightgbm_train_real_preds.csv", index=False)

# # -------------------------------------------------------
# # Save predictions for Wilcoxon test
# # -------------------------------------------------------
# lightgbm_preds_path = "modelB/lightGBM/lightgbm_train_synthetic_preds.csv"
# prop_level.to_csv(lightgbm_preds_path, index=False)

# print("Saved LightGBM synthetic predictions to", lightgbm_preds_path)
