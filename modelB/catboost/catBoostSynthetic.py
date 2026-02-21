import json
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import r2_score
import numpy as np
from sklearn.model_selection import ParameterGrid
import pandas as pd


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

# Split features and target
X_train = train_exp[features]
y_train = train_exp[target]

X_val = val_exp[features]
y_val = val_exp[target]

# -------------------------------------------------------
# Specify training and validation data
# -------------------------------------------------------

train_pool = Pool(X_train, y_train)
val_pool = Pool(X_val, y_val,)

# -------------------------------------------------------
# Hyperparameter grid for tuning
# We test multiple combinations to find best performance
# -------------------------------------------------------
param_grid = {
    "depth": [6, 8, 10],
    "learning_rate": [0.03, 0.05, 0.1],
    "l2_leaf_reg": [3, 5, 7],
    "iterations": [1500, 2000],
}

best_r2 = -np.inf
best_params = None
best_model = None

# -------------------------------------------------------
# Grid search over parameter combinations
# -------------------------------------------------------
# for params in ParameterGrid(param_grid):
#     model = CatBoostRegressor(
#         loss_function="RMSE",
#         eval_metric="R2",
#         random_seed=42,
#         verbose=False,
#         **params
#     )

#     # Train model with early stopping
#     model.fit(
#         train_pool,
#         eval_set=val_pool,
#         use_best_model=True,
#         early_stopping_rounds=100,
#     )

#     # Predict on validation set
#     val_preds = model.predict(X_val)

#     # ---------------------------------------------------
#     # Aggregate predictions to property level
#     # Multiple rows may belong to same property
#     # ---------------------------------------------------
#     pred_df = pd.DataFrame({
#         "source_row": val_exp["source_row"].values,
#         "y_true": y_val.values,
#         "y_pred": val_preds,
#     })

#     prop_level = pred_df.groupby("source_row", as_index=False).agg(
#         y_true=("y_true", "first"),
#         y_pred=("y_pred", "mean"),
#     )

#     # Compute metrics
#     r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
#     val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

#     # Track best performing model
#     if r2 > best_r2:
#         best_r2 = r2
#         best_params = params
#         best_model = model

#     print("tested:", params, "R2:", r2, "MAPE:", val_mape)

# print("\nbest R2:", best_r2)
# print("best params:", best_params)

# # -------------------------------------------------------
# # Save best parameters to JSON
# # -------------------------------------------------------
# params_path = "modelB/models/catBoost/synthetic_catboost_best_params2.json"

# params_to_save = {
#     "model_params": best_params,
#     "feature_columns": features
# }

# with open(params_path, "w") as f:
#     json.dump(params_to_save, f, indent=2)

# print("saved params and feature columns to:", params_path)


# # -------------------------------------------------------
# # Load best parameters from saved JSON
# # -------------------------------------------------------
# with open("modelB/models/catBoost/synthetic_catboost_best_params2.json", "r") as f:
#     saved = json.load(f)

# best_params = saved["model_params"]
# features = saved["feature_columns"]


# # -------------------------------------------------------
# # Train final model using best parameters
# # -------------------------------------------------------
# model = CatBoostRegressor(
#     loss_function="RMSE",
#     eval_metric="R2",
#     random_seed=42,
#     verbose=200,
#     **best_params,
# )

# model.fit(
#     train_pool,
#     eval_set=val_pool,
#     use_best_model=True,
#     early_stopping_rounds=100,
# )

# # -------------------------------------------------------
# # Save best model
# # -------------------------------------------------------
# model_path = "modelB/models/catBoost/synthetic_catboost_best_model2.cbm"
# best_model.save_model(model_path)
# print("saved model to:", model_path)

# -------------------------------------------------------
# Load best model for final predictions
# -------------------------------------------------------
model = CatBoostRegressor()
model.load_model("modelB/models/catBoost/synthetic_catboost_best_model2.cbm")

# -------------------------------------------------------
# Evaluate on synthetic test set
# -------------------------------------------------------

# test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")
# test_exp = test_exp.dropna(subset=[target])

# X_test = test_exp[features]
# y_test = test_exp[target]

# # Predict
# test_preds = model.predict(X_test)

# # Aggregate to property level
# pred_df_test = pd.DataFrame({
#     "source_row": test_exp["source_row"].values,
#     "y_true": y_test.values,
#     "y_pred": test_preds,
# })

# prop_level_test = pred_df_test.groupby("source_row", as_index=False).agg(
#     y_true=("y_true", "first"),
#     y_pred=("y_pred", "mean"),
# )

# # Metrics
# test_r2 = r2_score(prop_level_test["y_true"], prop_level_test["y_pred"])
# test_mape = mape(prop_level_test["y_true"], prop_level_test["y_pred"])

# print("Synthetic Test R2:", test_r2)
# print("Synthetic Test MAPE:", test_mape)


# -------------------------------------------------------
# Evaluate on real data
# -------------------------------------------------------

real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# Ground truth (post renovation value)
y_true = real_df["price"].astype(float)

# Preprocess features
real_df_processed = preprocess_real_data(real_df)

# Ensure feature alignment
real_X = real_df_processed[features]

real_preds = model.predict(real_X)

r2 = r2_score(y_true, real_preds)
real_mape = mape(y_true, real_preds)

print("Real Data R2:", r2)
print("Real Data MAPE:", real_mape)

# -------------------------------------------------------
# Save feature order
# -------------------------------------------------------
feature_cols_path = "modelB/models/synthetic_feature_columns2.json"

with open(feature_cols_path, "w") as f:
    json.dump(features, f, indent=2)


# -------------------------------------------------------
# Save predictions for Wilcoxon test 
# -------------------------------------------------------
catboost_preds_path = "modelB/catBoost/catboost_train_real_preds.csv"

pred_df = pd.DataFrame({
    "source_row": real_df.index,
    "y_true": y_true.values,
    "y_pred": real_preds
})

pred_df.to_csv(catboost_preds_path, index=False)

print(f"Saved CatBoost synthetic predictions to {catboost_preds_path}")
