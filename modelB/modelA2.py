import numpy as np
import pandas as pd

from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.metrics import r2_score
from catboost import CatBoostRegressor

train_df = pd.read_csv("processed_data/real_with_extracted_features_synonyms.csv")
val_df = pd.read_csv("processed_data/real_val_preprocessed.csv")

#remove duplicates
train_df = train_df.drop_duplicates().reset_index(drop=True)
val_df = val_df.drop_duplicates().reset_index(drop=True)

#spot outliers
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
if "material_grade" not in val_df.columns:
    val_df["material_grade"] = np.nan

material_mapping = {
    "budget-friendly": 0,
    "mid-range": 1,
    "high-end": 2
}

train_df["material_grade"] = train_df["material_grade"].map(material_mapping)
val_df["material_grade"] = val_df["material_grade"].map(material_mapping)


#label encode structural changes
if "structural_changes" in train_df.columns:
    le_structural = LabelEncoder()

    train_df["structural_changes"] = le_structural.fit_transform(
        train_df["structural_changes"].astype(str)
    )

    if "structural_changes" in val_df.columns:
        val_df["structural_changes"] = le_structural.transform(
            val_df["structural_changes"].astype(str)
        )
    else:
        val_df["structural_changes"] = np.nan
else:
    raise ValueError("structural_changes missing from training data")

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
if "type_of_renovation" in val_df.columns:
    val_df = pd.get_dummies(
        val_df,
        columns=["type_of_renovation"],
        dummy_na=True
    )
else:
    # create a dummy NaN column so alignment works
    val_df["type_of_renovation_nan"] = 1

train_df, val_df = train_df.align(
    val_df,
    join="left",
    axis=1,
    fill_value=0
)

#robust scale
target_col = "price"

exclude_cols = [
    target_col,
    "description"
]

feature_cols = [
    c for c in train_df.columns
    if c not in exclude_cols
]

scaler = RobustScaler()

train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
val_df[feature_cols] = scaler.transform(val_df[feature_cols])

X_train = train_df[feature_cols].values
y_train = np.log1p(train_df["price"].values)

X_val = val_df[feature_cols].values
y_val_log = np.log1p(val_df["price"].values)

#train model
model = CatBoostRegressor(
    iterations=1500,
    depth=8,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    early_stopping_rounds=100,
    verbose=100
)

model.fit(
    X_train,
    y_train,
    eval_set=(X_val, y_val_log)
)

val_preds_log = model.predict(X_val)
r2 = r2_score(y_val_log, val_preds_log)

print("A2 R^2 (log price):", r2)
