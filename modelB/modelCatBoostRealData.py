import numpy as np
import pandas as pd

from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score
from catboost import CatBoostRegressor
from itertools import product
import json

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))

train_df = pd.read_csv("processed_data/real_with_extracted_features_synonyms.csv")
val_df = pd.read_csv("processed_data/real_val_with_extracted_features_synonyms.csv")

#remove duplicates
train_df = train_df.drop_duplicates().reset_index(drop=True)
val_df = val_df.drop_duplicates().reset_index(drop=True)

#spot outliers for price and remove them
Q1 = train_df["price"].quantile(0.25)
Q3 = train_df["price"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

train_df = train_df[
    (train_df["price"] >= lower) &
    (train_df["price"] <= upper)
].reset_index(drop=True)

#ordinally encode material grade
material_mapping = {
    "budget-friendly": 0,
    "mid-range": 1,
    "high-end": 2
}

# ensure column exists in both
for df in [train_df, val_df]:
    if "material_grade" not in df.columns:
        df["material_grade"] = np.nan

# apply the same ordinal mapping to both
train_df["material_grade"] = train_df["material_grade"].map(material_mapping)
val_df["material_grade"] = val_df["material_grade"].map(material_mapping)



#label encode structural changes
# ensure column exists in both datasets
for df in [train_df, val_df]:
    if "structural_changes" not in df.columns:
        df["structural_changes"] = np.nan

# fit encoder on training data only
le_structural = LabelEncoder()

train_df["structural_changes"] = le_structural.fit_transform(
    train_df["structural_changes"].astype(str)
)

# apply same encoding to validation
val_df["structural_changes"] = le_structural.transform(
    val_df["structural_changes"].astype(str)
)

#one hot encode reno type
# one hot encode renovation type on train
if "type_of_renovation" in train_df.columns:
    train_df = pd.get_dummies(
        train_df,
        columns=["type_of_renovation"],
        dummy_na=True
    )
else:
    raise ValueError("type_of_renovation missing from training data")

# one hot encode renovation type on validation only if present
# ensure column exists in both datasets
for df in [train_df, val_df]:
    if "type_of_renovation" not in df.columns:
        df["type_of_renovation"] = np.nan

# one hot encode BOTH together to guarantee identical columns
combined = pd.concat(
    [train_df, val_df],
    axis=0,
    ignore_index=True
)

combined = pd.get_dummies(
    combined,
    columns=["type_of_renovation"],
    dummy_na=True
)

# split back into train and validation
train_df = combined.iloc[:len(train_df)].reset_index(drop=True)
val_df = combined.iloc[len(train_df):].reset_index(drop=True)


#apply trained catboot to validation set
target_col = "price"

exclude_cols = [
    target_col,
    "description"
]

feature_cols = [
    c for c in train_df.columns
    if c not in exclude_cols
]

#remove very high or very small property sizes
lower = train_df["property_size"].quantile(0.01)
upper = train_df["property_size"].quantile(0.99)

for df in [train_df, val_df]:
    df["property_size"] = df["property_size"].clip(lower, upper)


X_train = train_df[feature_cols].values
y_train = np.log1p(train_df["price"].values)

X_val = val_df[feature_cols].values
y_val_log = np.log1p(val_df["price"].values)

#train model
param_grid = {
    "depth": [4, 6, 8],
    "learning_rate": [0.03, 0.1, 0.15],
    "l2_leaf_reg": [3, 8, 15]
}

results = []
best_r2 = -np.inf
best_model = None
best_params = None

for depth, lr, l2 in product(
    param_grid["depth"],
    param_grid["learning_rate"],
    param_grid["l2_leaf_reg"]
):
    model = CatBoostRegressor(
        iterations=1500,
        depth=depth,
        learning_rate=lr,
        l2_leaf_reg=l2,
        #changed loss function from RMSE to MAE to improve MAPE
        loss_function="MAE",
        random_seed=42,
        early_stopping_rounds=100,
        verbose=False
    )

    model.fit(
        X_train,
        y_train,
        eval_set=(X_val, y_val_log)
    )

    preds = model.predict(X_val)
    r2 = r2_score(y_val_log, preds)

    results.append({
        "depth": depth,
        "learning_rate": lr,
        "l2_leaf_reg": l2,
        "r2": r2,
        "best_iter": model.get_best_iteration()
    })

    if r2 > best_r2:
        best_r2 = r2
        best_model = model
        best_params = (depth, lr, l2)

#save the model
model_path = "modelB/models/A2_catboost_model.cbm"
best_model.save_model(model_path)

print(f"Model saved")
best_params_dict = {
    "depth": best_params[0],
    "learning_rate": best_params[1],
    "l2_leaf_reg": best_params[2]
}

#save hyperparams
params_path = "modelB/models/A2_catboost_params.json"

with open(params_path, "w") as f:
    json.dump(best_params_dict, f, indent=4)

print(f"Parameters saved")

#save feature column order
feature_cols_path = "modelB/models/A2_feature_columns.json"

with open(feature_cols_path, "w") as f:
    json.dump(feature_cols, f, indent=4)

print(f"Feature columns saved to {feature_cols_path}")

# results table
results_df = pd.DataFrame(results).sort_values("r2", ascending=False)

print(results_df.head())
print("\nBest params:")
print("depth:", best_params[0])
print("learning_rate:", best_params[1])
print("l2_leaf_reg:", best_params[2])
print("Best R^2:", best_r2)

# predict log price on validation
val_preds_log = best_model.predict(X_val)

# convert back to original price scale
val_preds_price = np.expm1(val_preds_log)
y_val_price = val_df["price"].values

# R^2 on log price (already correct)
final_r2 = r2_score(y_val_log, val_preds_log)

# MAPE on original price
mape = mean_absolute_percentage_error(y_val_price, val_preds_price)

print("Final A2 R^2 (log price):", final_r2)
print("Final A2 MAPE:", mape)
print("Final A2 MAPE (%):", mape * 100)