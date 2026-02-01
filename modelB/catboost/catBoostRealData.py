import numpy as np
import pandas as pd
import ast
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
# ensure column exists
for df_ in [train_df, val_df]:
    if "type_of_renovation" not in df_.columns:
        df_["type_of_renovation"] = ""

def normalize_token(x):
    return " ".join(x.lower().strip().split())

def parse_reno(value):
    if pd.isna(value):
        return []

    value = str(value)

    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [normalize_token(v) for v in parsed if isinstance(v, str)]
        except Exception:
            return []

    return [normalize_token(value)]
train_df["type_of_renovation_parsed"] = train_df["type_of_renovation"].apply(parse_reno)
val_df["type_of_renovation_parsed"] = val_df["type_of_renovation"].apply(parse_reno)

# fixed schema
fixed_types = {
    "bathroom": "bathroom",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
    "living room": "living_room",
    "other/custom": "other_custom",
    "full renovation": "full_renovation"
}

for key, suffix in fixed_types.items():
    col = f"reno_{suffix}"
    train_df[col] = train_df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))
    val_df[col] = val_df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))

# drop source columns
train_df = train_df.drop(columns=["type_of_renovation", "type_of_renovation_parsed"])
val_df = val_df.drop(columns=["type_of_renovation", "type_of_renovation_parsed"])

# align columns
train_df, val_df = train_df.align(val_df, join="left", axis=1, fill_value=0)

#see the real features
train_processed_path = "processed_data/real_features.csv"

if "id" in train_df.columns:
    train_df = train_df.drop(columns=["id"])
train_df.to_csv(train_processed_path, index=False)

#apply trained catboot to validation set
target_col = "price"

exclude_cols = [
    target_col,
    "description"
]

DROP_FEATURES = [
    "id",
    "num_of_bedrooms",
    "num_of_bathrooms"
]

feature_cols = [
    c for c in train_df.columns
    if c not in exclude_cols and c not in DROP_FEATURES
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
model_path = "modelB/models/real_catboost_model.cbm"
best_model.save_model(model_path)

print(f"Model saved")
best_params_dict = {
    "depth": best_params[0],
    "learning_rate": best_params[1],
    "l2_leaf_reg": best_params[2]
}

#save hyperparams
params_path = "modelB/models/real_catboost_params.json"

with open(params_path, "w") as f:
    json.dump(best_params_dict, f, indent=4)

print(f"Parameters saved")

#save feature column order
feature_cols_path = "modelB/models/real_feature_columns.json"

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

# save predictions for Wilcoxon test (real data, CatBoost)
catboost_preds_path = "modelB/catBoost/catboost_real_preds.csv"

pred_df = pd.DataFrame({
    "id": val_df.index,
    "y_true": y_val_price,
    "y_pred": val_preds_price
})

pred_df.to_csv(catboost_preds_path, index=False)

print(f"Saved CatBoost real predictions to {catboost_preds_path}")


# R^2 on log price (already correct)
final_r2 = r2_score(y_val_log, val_preds_log)

# MAPE on original price
mape = mean_absolute_percentage_error(y_val_price, val_preds_price)

print("Final A2 R^2 (log price):", final_r2)
print("Final A2 MAPE:", mape)
print("Final A2 MAPE (%):", mape * 100)