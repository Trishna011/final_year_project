from datasets import load_dataset
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import RobustScaler, LabelEncoder, PolynomialFeatures
import category_encoders as ce
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, train_test_split, KFold
from sklearn.linear_model import LassoCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, make_scorer, root_mean_squared_error, mean_absolute_error,r2_score
import numpy as np
import shap, xgboost
import json
from mlxtend.plotting import heatmap
import joblib
import os
import re
import ast
from sentence_transformers import SentenceTransformer
from catboost import CatBoostRegressor


#load the dataset from hugging face
dataset = load_dataset("Trish101/reno_details_dataset", split="train")
df = dataset.to_pandas()
#get rid of duplicate rows
df = df.drop_duplicates()
print("After removing duplicates:", df.shape)

#lightly preprocess post-reno desc by lowercasing, removing white spaces and normalising
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.lower()
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text

df["post_renovation_description"] = df["post_renovation_description"].apply(clean_text)

#spotting outliers
def extract_sqft(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            data = ast.literal_eval(value)
            total = 0
            for k in ["bedrooms", "bathrooms", "other"]:
                if k in data and isinstance(data[k], list):
                    total += sum([v for v in data[k] if isinstance(v, (int, float))])
            return total
        except:
            return np.nan
    return np.nan

# remove logically invalid and economically impossible rows
df = df[
    (df["property_size"] > 0) &
    (df["pre_renovation_cost"] > 0) &
    (df["renovation_cost"] >= 0) &
    (df["renovation_cost"] <= df["pre_renovation_cost"] * 2)
]

print("After rule based filtering:", df.shape)


# define numeric columns for IQR
iqr_cols = [
    "renovation_cost",
    "pre_renovation_cost",
    "property_size",
]

cols_with_outliers = []

for col in iqr_cols:
    clean_col = df[col].dropna()
    Q1 = clean_col.quantile(0.25)
    Q3 = clean_col.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = df[(df[col] < lower) | (df[col] > upper)]

    if len(outliers) > 0:
        cols_with_outliers.append(col)

    print(f"{col}: {len(outliers)} outliers")

# rule based checks for bedroom and bathroom counts
def count_outliers(series, max_allowed):
    invalid = series[(series < 0) | (series % 1 != 0) | (series > max_allowed)]
    return invalid

bedroom_outliers = count_outliers(df["bedrooms_to_reno"], 10)
bathroom_outliers = count_outliers(df["bathrooms_to_reno"], 10)

print("bedrooms_to_reno outliers:", len(bedroom_outliers))
print("bathrooms_to_reno outliers:", len(bathroom_outliers))

df = df[
    (df["bedrooms_to_reno"] >= 0) &
    (df["bedrooms_to_reno"] % 1 == 0) &
    (df["bedrooms_to_reno"] <= 10) &
    (df["bathrooms_to_reno"] >= 0) &
    (df["bathrooms_to_reno"] % 1 == 0) &
    (df["bathrooms_to_reno"] <= 10)
]

# plot boxplots for IQR based columns
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[cols_with_outliers])
plt.xticks(rotation=45)
#plt.show()

# ordinal encode material_grade
grade_map = {
    "budgetfriendly": 0,
    "midrange": 1,
    "highend": 2
}

def normalize_grade(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().replace("-", "").replace(" ", "")
    return text

# -------------------------------
# synthetic post renovation value
# -------------------------------

# -------------------------------
# synthetic post renovation value
# realistic formulation
# -------------------------------

BASE_UPLIFT = 0.015
MAX_TOTAL_UPLIFT = 0.18

def compute_renovation_uplift(row):
    uplift = BASE_UPLIFT

    uplift += 0.03 * ("Kitchen" in str(row.get("renovation_type", "")))
    uplift += 0.015 * ("Bathroom" in str(row.get("renovation_type", "")))
    uplift += 0.03 * ("Full renovation" in str(row.get("renovation_type", "")))
    

    uplift += min(
        row.get("sqft_to_add_num", 0) / max(row.get("property_size", 1), 1),
        0.10
    )

    return min(uplift, MAX_TOTAL_UPLIFT)


def compute_material_multiplier(value):
    if pd.isna(value):
        return 1.0

    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            return 1.0

    if not isinstance(value, dict):
        return 1.0

    grades = []

    for room in ["bedrooms", "bathrooms"]:
        entries = value.get(room, [])
        if isinstance(entries, list):
            for g in entries:
                key = normalize_grade(g)
                grades.append(grade_map.get(key, 0))

    other = value.get("other", {})
    if isinstance(other, dict):
        for g in other.values():
            key = normalize_grade(g)
            grades.append(grade_map.get(key, 0))

    if not grades:
        return 1.0

    return 1.0 + 0.05 * (sum(grades) / len(grades))


renovation_uplift = df.apply(compute_renovation_uplift, axis=1)
material_multiplier = df["material_grade"].apply(compute_material_multiplier)

# cost influence ratio (bounded)
cost_ratio = (
    df["renovation_cost"] / df["pre_renovation_cost"]
).clip(upper=0.5)

df["post_renovation_value"] = (
    df["pre_renovation_cost"]
    * (
        1
        + renovation_uplift
        + 0.3 * cost_ratio * material_multiplier
    )
)


# df["renovation_value_uplift_pct"] = (
#     (df["post_renovation_value"] - df["pre_renovation_cost"])
#     / df["pre_renovation_cost"]
# ) * 100

# df["pre_reno"] = (
#     df["pre_renovation_cost"]
# )

# uplift_pct = df["renovation_value_uplift_pct"]

# print(uplift_pct.describe())
# print("Share above 20%:", (uplift_pct > 20).mean())
# print("Share above 25%:", (uplift_pct > 25).mean())
# print("Share above 30%:", (uplift_pct > 30).mean())


#Data split synthetic data as 80% train and 20% test
train_df, val_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    shuffle=True
)

print("Training rows:", train_df.shape)
print("Validation rows:", val_df.shape)


#label encode struct changes
struct_map = {
    "Yes": 1,
    "No": 0
}

def encode_structural_changes_lists(value):
    if pd.isna(value):
        return []

    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            return []

    if not isinstance(value, list):
        return []

    return [struct_map.get(v, 0) for v in value]


train_df["structural_changes"] = train_df["structural_changes"].apply(encode_structural_changes_lists)
val_df["structural_changes"] = val_df["structural_changes"].apply(encode_structural_changes_lists)

#target encode location
target_col = "post_renovation_value"

kf = KFold(n_splits=5, shuffle=True, random_state=42)

train_df["location"] = 0.0
global_mean = train_df[target_col].mean()

for train_idx, val_idx in kf.split(train_df):
    fold_train = train_df.iloc[train_idx]
    fold_val = train_df.iloc[val_idx]

    location_means = fold_train.groupby("location")[target_col].mean()

    train_df.loc[fold_val.index, "location"] = (
        fold_val["location"].map(location_means).fillna(global_mean)
    )

# fit final mapping on full training set
location_means_full = train_df.groupby("location")[target_col].mean()

val_df["location"] = (
    val_df["location"].map(location_means_full).fillna(global_mean)
)



def encode_material_grade_lists(value):
    if pd.isna(value):
        return {}

    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            return {}

    if not isinstance(value, dict):
        return {}

    encoded = {}

    # bedrooms and bathrooms are lists of grades
    for room_type in ["bedrooms", "bathrooms"]:
        entries = value.get(room_type, [])
        if isinstance(entries, list):
            encoded_list = []
            for g in entries:
                key = normalize_grade(g)
                encoded_list.append(grade_map.get(key, 0))
            if encoded_list:
                encoded[room_type] = encoded_list

    # other is a dict of {space_name: grade_string}
    other_entries = value.get("other", {})
    if isinstance(other_entries, dict):
        other_encoded = {}
        for k, g in other_entries.items():
            key = normalize_grade(g)
            other_encoded[k] = grade_map.get(key, 0)
        if other_encoded:
            encoded["other"] = other_encoded

    return encoded


train_df["material_grade"] = train_df["material_grade"].apply(encode_material_grade_lists)
val_df["material_grade"] = val_df["material_grade"].apply(encode_material_grade_lists)

# one hot encode renovation_type for now
# replace dynamic category discovery with a fixed, complete schema
fixed_types = [
    "Bathroom",
    "Bedroom",
    "Kitchen",
    "Living room",
    "Other/Custom",
    "Full renovation"
]

for t in fixed_types:
    col_name = f"reno_{t.lower().replace(' ', '_').replace('/', '_')}"
    train_df[col_name] = train_df["renovation_type"].apply(lambda x: int(t in x))
    val_df[col_name] = val_df["renovation_type"].apply(lambda x: int(t in x))

train_df, val_df = train_df.align(val_df, join="left", axis=1, fill_value=0)

train_df = train_df.drop(columns=["renovation_type"])
val_df = val_df.drop(columns=["renovation_type"])


# create output folders
os.makedirs("processed_data", exist_ok=True)
os.makedirs("preprocessing_artifacts", exist_ok=True)

# helper to safely serialize lists and dicts
def to_json_safe(x):
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return json.dumps(None)

# serialize complex columns before saving
for col in ["structural_changes", "material_grade"]:
    train_df[col] = train_df[col].apply(to_json_safe)
    val_df[col] = val_df[col].apply(to_json_safe)

# save processed datasets
train_path = os.path.join("processed_data", "synthetic_train_preprocessed.csv")
val_path = os.path.join("processed_data", "synthetic_val_preprocessed.csv")

FEATURE_COLS = train_df.drop(columns=["post_renovation_value"]).columns.tolist()

with open(
    "preprocessing_artifacts/feature_columns.json",
    "w"
) as f:
    json.dump(FEATURE_COLS, f)


train_df.to_csv(train_path, index=False)
val_df.to_csv(val_path, index=False)

print("Saved train data to:", train_path)
print("Saved validation data to:", val_path)