from datasets import load_dataset
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, KFold
import numpy as np
import json
from mlxtend.plotting import heatmap
import os
import ast
from pathlib import Path

# -----------------------------
# Load synthetic renovation dataset from hugging face and test set from local csv
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR
test_set = PROJECT_ROOT.parent / "test_synthetic_renovation_scenarios_with_pre_cost.csv"

dataset = load_dataset("Trish101/reno_details_dataset", split="train")
test_dataset = pd.read_csv(test_set)

# Convert to pandas DataFrame
df = dataset.to_pandas()
test_df = dataset.to_pandas()

#get rid of duplicate rows
df = df.drop_duplicates()
test_df = test_df.drop_duplicates()
print("After removing duplicates:", df.shape)


# -----------------------------
# Helper to extract total square footage from nested fields
# -----------------------------
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

# Remove logically invalid or economically impossible rows

def remove_invalid_rows(df):
    df = df[
        (df["property_size"] > 0) &
        (df["pre_renovation_cost"] > 0) &
        (df["renovation_cost"] >= 0) &
        (df["renovation_cost"] <= df["pre_renovation_cost"] * 2)
    ]
    return df
df = remove_invalid_rows(df)
test_df = remove_invalid_rows(test_df)

def remove_invaid_bath_bed(df):
    # Bedrooms and bathrooms must:
    # - Be non negative
    # - Be whole numbers
    # - Not exceed 10
    df = df[
        (df["bedrooms_to_reno"] >= 0) &
        (df["bedrooms_to_reno"] % 1 == 0) &
        (df["bedrooms_to_reno"] <= 10) &
        (df["bathrooms_to_reno"] >= 0) &
        (df["bathrooms_to_reno"] % 1 == 0) &
        (df["bathrooms_to_reno"] <= 10)
    ]
    return df
df = remove_invaid_bath_bed(df)
test_df = remove_invaid_bath_bed(test_df)

# -----------------------------
# Outlier detection using IQR - only for visualisation purposes
# -----------------------------
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


# plot boxplots for IQR based columns
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[cols_with_outliers])
plt.xticks(rotation=45)
#plt.show()

# -------------------------------
# Encode categorical features
# -------------------------------

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

BASE_UPLIFT = 0.015
MAX_TOTAL_UPLIFT = 0.18

def compute_renovation_uplift(row):
    uplift = BASE_UPLIFT

    # Kitchen and full renovations add higher value
    uplift += 0.03 * ("Kitchen" in str(row.get("renovation_type", "")))
    uplift += 0.015 * ("Bathroom" in str(row.get("renovation_type", "")))
    uplift += 0.03 * ("Full renovation" in str(row.get("renovation_type", "")))
    
    # Adding square footage increases value
    uplift += min(
        row.get("sqft_to_add_num", 0) / max(row.get("property_size", 1), 1),
        0.10
    )

    # Cap total uplift for realism
    return min(uplift, MAX_TOTAL_UPLIFT)

#This part converts material quality into a numeric multiplier that increases the post renovation property value.
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
renovation_uplift_test = test_df.apply(compute_renovation_uplift, axis=1)

material_multiplier = df["material_grade"].apply(compute_material_multiplier)
material_multiplier_test = test_df["material_grade"].apply(compute_material_multiplier)

# measures how large the renovation is relative to the house value, then limits its influence for realism and stability.
cost_ratio = (
    df["renovation_cost"] / df["pre_renovation_cost"]
).clip(upper=0.5)

cost_ratio_test = (
    test_df["renovation_cost"] / test_df["pre_renovation_cost"]
).clip(upper=0.5)

# Estimate post renovation value for synthetic data
df["post_renovation_value"] = (
    df["pre_renovation_cost"]
    * (
        1
        + renovation_uplift
        + 0.3 * cost_ratio * material_multiplier
    )
)

test_df["post_renovation_value"] = (
    test_df["pre_renovation_cost"]
    * (
        1
        + renovation_uplift
        + 0.3 * cost_ratio * material_multiplier
    )
)


#Data split synthetic data as 80% train and 20% val
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

#for test set
test_df["structural_changes"] = test_df["structural_changes"].apply(encode_structural_changes_lists)

# target encoding on the location feature using KFold to prevent leakage.
target_col = "post_renovation_value"

kf = KFold(n_splits=5, shuffle=True, random_state=42)

train_df["location_te"] = 0.0
global_mean = train_df[target_col].mean()

for train_idx, val_idx in kf.split(train_df):
    fold_train = train_df.iloc[train_idx]
    fold_val = train_df.iloc[val_idx]

    location_means = fold_train.groupby("location")[target_col].mean()

    train_df.loc[fold_val.index, "location_te"] = (
        fold_val["location"].map(location_means).fillna(global_mean)
    )

# fit final mapping on full training set
location_means_full = train_df.groupby("location")[target_col].mean()

val_df["location_te"] = (
    val_df["location"].map(location_means_full).fillna(global_mean)
)

# for test set
test_df["location_te"] = (
    test_df["location"].map(location_means_full).fillna(global_mean)
)

train_df = train_df.drop(columns=["location"])
val_df = val_df.drop(columns=["location"])
test_df = test_df.drop(columns=["location"])

train_df["location"] = train_df["location_te"]
val_df["location"] = val_df["location_te"]
test_df["location"] = test_df["location_te"]

train_df = train_df.drop(columns=["location_te"])
val_df = val_df.drop(columns=["location_te"])
test_df = test_df.drop(columns=["location_te"])

# Encode each item in the material grade list
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
test_df["material_grade"] = test_df["material_grade"].apply(encode_material_grade_lists)

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
    test_df[col_name] = test_df["renovation_type"].apply(lambda x: int(t in x))
    

train_df, val_df = train_df.align(val_df, join="left", axis=1, fill_value=0)
test_df = test_df.reindex(columns=train_df.columns, fill_value=0)

train_df = train_df.drop(columns=["renovation_type"])
val_df = val_df.drop(columns=["renovation_type"])
test_df = test_df.drop(columns=["renovation_type"])


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
    test_df[col] = test_df[col].apply(to_json_safe)

# save processed datasets
train_path = os.path.join("processed_data", "synthetic_train_preprocessed.csv")
val_path = os.path.join("processed_data", "synthetic_val_preprocessed.csv")
test_path = os.path.join("processed_data", "synthetic_test_preprocessed.csv")


#save feature columns to use for user inputs
FEATURE_COLS = train_df.drop(columns=["post_renovation_value"]).columns.tolist()

with open(
    "preprocessing_artifacts/feature_columns.json",
    "w"
) as f:
    json.dump(FEATURE_COLS, f)


train_df.to_csv(train_path, index=False)
val_df.to_csv(val_path, index=False)
test_df.to_csv(test_path, index=False)

print("Saved train data to:", train_path)
print("Saved validation data to:", val_path)
print("Saved test data to:", test_path)