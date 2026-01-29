import json
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import r2_score
import numpy as np
from sklearn.model_selection import ParameterGrid
import pandas as pd


train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")

def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan

    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


#TRAIN CATBOOST
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

cat_features = [X_train.columns.get_loc("unit_type")]

train_pool = Pool(X_train, y_train, cat_features=cat_features)
val_pool = Pool(X_val, y_val, cat_features=cat_features)


param_grid = {
    "depth": [6, 8, 10],
    "learning_rate": [0.03, 0.05, 0.1],
    "l2_leaf_reg": [3, 5, 7],
    "iterations": [1500, 2000],
}

best_r2 = -np.inf
best_params = None
best_model = None

# for params in ParameterGrid(param_grid):
#     model = CatBoostRegressor(
#         loss_function="RMSE",
#         eval_metric="R2",
#         random_seed=42,
#         verbose=False,
#         **params
#     )

#     model.fit(
#         train_pool,
#         eval_set=val_pool,
#         use_best_model=True,
#         early_stopping_rounds=100,
#     )

#     val_preds = model.predict(X_val)

#     pred_df = pd.DataFrame({
#         "source_row": val_exp["source_row"].values,
#         "y_true": y_val.values,
#         "y_pred": val_preds,
#     })val_preds = n

#     prop_level = pred_df.groupby("source_row", as_index=False).agg(
#         y_true=("y_true", "first"),
#         y_pred=("y_pred", "mean"),
#     )

#     r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
#     val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

#     if r2 > best_r2:
#         best_r2 = r2
#         best_params = params
#         best_model = model

#     print("tested:", params, "R2:", r2, "MAPE:", val_mape)

# print("\nbest R2:", best_r2)
# print("best params:", best_params)

# load best params
with open("modelB/models/synthetic_catboost_params.json", "r") as f:
    best_params = json.load(f)

# train final model using best params
model = CatBoostRegressor(
    loss_function="RMSE",
    eval_metric="R2",
    random_seed=42,
    verbose=200,
    **best_params,
)

model.fit(
    train_pool,
    eval_set=val_pool,
    use_best_model=True,
    early_stopping_rounds=100,
)

# predict using the best model
val_preds = model.predict(X_val)

# build prediction dataframe
pred_df = pd.DataFrame({
    "source_row": val_exp["source_row"].values,
    "y_true": y_val.values,
    "y_pred": val_preds,
})

# aggregate back to property level
prop_level = pred_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean"),
)

# metrics
r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
val_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("final R2 with best params:", r2)
print("final MAPE with best params:", val_mape)

#save the feature order
feature_cols_path = "modelB/models/synthetic_feature_columns.json"

with open(feature_cols_path, "w") as f:
    json.dump(features, f, indent=2)

# # save best model
# model_path = "modelB/models/synthetic_catboost_best_model.cbm"
# best_model.save_model(model_path)
# print("saved model to:", model_path)

# # save best params
# params_path = "modelB/models/synthetic_catboost_best_params.json"
# with open(params_path, "w") as f:
#     json.dump(best_params, f, indent=2)

# print("saved params to:", params_path)
