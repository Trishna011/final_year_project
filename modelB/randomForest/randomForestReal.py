import numpy as np
import pandas as pd
import ast
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
import json

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))


# load data
train_df = pd.read_csv("processed_data/real_with_extracted_features_synonyms.csv")
val_df = pd.read_csv("processed_data/real_val_with_extracted_features_synonyms.csv")

# remove duplicates
train_df = train_df.drop_duplicates().reset_index(drop=True)
val_df = val_df.drop_duplicates().reset_index(drop=True)

# remove outliers
Q1 = train_df["price"].quantile(0.25)
Q3 = train_df["price"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

train_df = train_df[
    (train_df["price"] >= lower) &
    (train_df["price"] <= upper)
].reset_index(drop=True)

# ordinal encode material grade
material_mapping = {
    "budget-friendly": 0,
    "mid-range": 1,
    "high-end": 2
}

for df in [train_df, val_df]:
    df["material_grade"] = df.get("material_grade", np.nan).map(material_mapping)

# label encode structural changes
le_structural = LabelEncoder()
train_df["structural_changes"] = le_structural.fit_transform(
    train_df["structural_changes"].astype(str)
)
val_df["structural_changes"] = le_structural.transform(
    val_df["structural_changes"].astype(str)
)

# one hot encode renovation types
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

train_df = train_df.drop(columns=["type_of_renovation", "type_of_renovation_parsed"])
val_df = val_df.drop(columns=["type_of_renovation", "type_of_renovation_parsed"])

# align columns
train_df, val_df = train_df.align(val_df, join="left", axis=1, fill_value=0)

# feature selection
DROP_FEATURES = [
    "id",
    "num_of_bedrooms",
    "num_of_bathrooms",
    "description"
]

feature_cols = [
    c for c in train_df.columns
    if c not in DROP_FEATURES and c != "price"
]

# clip property size
lower = train_df["property_size"].quantile(0.01)
upper = train_df["property_size"].quantile(0.99)

for df in [train_df, val_df]:
    df["property_size"] = df["property_size"].clip(lower, upper)

X_train = train_df[feature_cols].values
y_train_log = np.log1p(train_df["price"].values)

X_val = val_df[feature_cols].values
y_val_log = np.log1p(val_df["price"].values)

# train Random Forest
rf_model = RandomForestRegressor(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train_log)

# predict
val_preds_log = rf_model.predict(X_val)

# back to price scale
val_preds_price = np.expm1(val_preds_log)
y_val_price = val_df["price"].values

# save predictions for Wilcoxon
rf_preds_path = "modelB/randomForest/randomforest_real_preds.csv"

pred_df = pd.DataFrame({
    "id": val_df.index,
    "y_true": y_val_price,
    "y_pred": val_preds_price
})

pred_df.to_csv(rf_preds_path, index=False)

print(f"Saved Random Forest real predictions to {rf_preds_path}")

# metrics
r2 = r2_score(y_val_log, val_preds_log)
mape = mean_absolute_percentage_error(y_val_price, val_preds_price)

print("Random Forest R^2 (log price):", r2)
print("Random Forest MAPE:", mape)
print("Random Forest MAPE (%):", mape * 100)
