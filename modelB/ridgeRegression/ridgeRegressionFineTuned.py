import numpy as np
import pandas as pd
import ast
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
import joblib
import random
import json


def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

# -----------------------------
# Normalize material text into consistent format
# -----------------------------
def normalize_material(x):
    if pd.isna(x):
        return np.nan
    return (
        str(x)
        .lower()
        .strip()
        .replace("_", "-")
        .replace(" ", "-")
    )

# -----------------------------
# Normalize renovation tokens
# -----------------------------
def normalize_token(x):
    return " ".join(x.lower().strip().split())

# -----------------------------
# Parse renovation type column into list format
# Converts string or list string into list format
# -----------------------------
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


# -----------------------------
# Preprocess real dataset to match synthetic schema
# -----------------------------
def preprocess_real(df, require_target=False):
    
    if "type_of_renovation" in df.columns:
        # Clean renovation type column
        df["type_of_renovation"] = df["type_of_renovation"].astype(str).str.strip().str.lower()
        df = df[~df["type_of_renovation"].isin(["", "nan", "none", "null"])]

        # Encode material grade ordinally
        material_mapping = {
            "budget-friendly": 0,
            "mid-range": 1,
            "high-end": 2
        }

        df["material_grade"] = df["material_grade"].apply(normalize_material)
        df["material_grade"] = df["material_grade"].map(material_mapping)
        df["material_grade"] = df["material_grade"].astype(float)

    
        # Parse renovation types into structured form
        df["type_of_renovation_parsed"] = df["type_of_renovation"].apply(parse_reno)

        # Create one hot features for renovation types
        fixed_types = {
            "bathroom": "bathroom",
            "bedroom": "bedroom",
            "kitchen": "kitchen",
            "living room": "living_room",
            "other/custom": "other_custom",
            "full renovation": "full_renovation"
        }

        for suffix in fixed_types.values():
            df[f"reno_{suffix}"] = 0

        for key, suffix in fixed_types.items():
            df[f"reno_{suffix}"] = df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))

        # Select first renovation type as categorical feature
        def choose_unit_type(lst):
            if not lst:
                return "unknown"
            return lst[0]

        df["unit_type"] = df["type_of_renovation_parsed"].apply(choose_unit_type)

        # Drop unused columns
        df = df.drop(
            columns=["type_of_renovation", "type_of_renovation_parsed", "Location", "id"],
            errors="ignore"
        )

        df["post_renovation_value"] = df["price"]

    else:
        # Ensure correct types
        df["material_grade"] = df["material_grade"].astype(float)
        df["unit_type"] = df["unit_type"].astype(str)

        # structural_change naming consistency
        if "structural_change" in df.columns:
            df["structural_changes"] = df["structural_change"].astype(int)

        df = df.drop(
            columns=["source_row"],
            errors="ignore"
        )
    return df

# -----------------------------
# Load pretrained synthetic model
# -----------------------------
syn_model = joblib.load("modelB/models/ridgeRegression/ridge_synthetic_model.pkl")

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
with open("modelB/models/ridgeRegression/ridge_synthetic_best_params.json", "r") as f:
    saved = json.load(f)

SYN_FEATURE_COLS = saved["feature_columns"]
SYN_MODEL_PARAMS = saved["model_params"]

# -----------------------------
# Prepare train_val set for fine-tuning
# ------------------------------
dev_df = pd.read_csv("processed_data/real_train_val_with_predicted_reno_cost.csv")

dev_df = preprocess_real(dev_df, require_target=True)


dev_df["post_renovation_value"] = dev_df["price"]

raw_feature_list = [
"property_size",
"location",
"renovation_cost",
"sqft_renovated",
"sqft_to_add",
"material_grade",
"structural_changes",
"unit_type",
"reno_bathroom",
"reno_bedroom",
"reno_kitchen",
"reno_living_room",
"reno_other_custom",
"reno_full_renovation"
]

X_dev_raw = dev_df[raw_feature_list]

X_dev_enc = pd.get_dummies(X_dev_raw, drop_first=True)

X_dev_enc = X_dev_enc.reindex(columns=SYN_FEATURE_COLS, fill_value=0)

X_dev = X_dev_enc
y_dev = dev_df["post_renovation_value"]
print(X_dev.describe())

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# -----------------------------
# Tune Ridge with AAEO
# -----------------------------
BOUNDS = {
    "alpha": (0.0001, 100.0)
}

# Random parameter generator
def random_individual():
    return {
        "alpha": np.random.uniform(*BOUNDS["alpha"])
    }

# Evaluate parameter set using 5 fold CV
def evaluate(individual):

    clean_params = {
        "alpha": float(individual["alpha"])
    }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    fold_scores = []

    for train_idx, val_idx in kf.split(X_dev):

        X_tr = X_dev.iloc[train_idx]
        y_tr = y_dev.iloc[train_idx]

        X_va = X_dev.iloc[val_idx]
        y_va = y_dev.iloc[val_idx]

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge", Ridge(**clean_params))
        ])

        model.fit(X_tr, y_tr)
        preds = model.predict(X_va)

        fold_scores.append(r2_score(y_va, preds))

    return np.mean(fold_scores)

# -----------------------------
# Evolutionary Search
# -----------------------------
POP_SIZE = 8
GENERATIONS = 10

population = [random_individual() for _ in range(POP_SIZE)]
fitness = [evaluate(ind) for ind in population]

best_idx = np.argmax(fitness)
best_individual = population[best_idx]
best_score = fitness[best_idx]

print("Initial best R2:", best_score)

for gen in range(GENERATIONS):
    print("\nGeneration", gen + 1)

    new_population = []

    for i, ind in enumerate(population):

        if random.random() < 0.5:
            partner = population[np.random.randint(POP_SIZE)]
            new_ind = {
                "alpha": ind["alpha"] + np.random.uniform(-0.2, 0.2) * (partner["alpha"] - ind["alpha"])
            }
        else:
            new_ind = {
                "alpha": ind["alpha"] + np.random.uniform(-0.1, 0.1)
            }

        new_ind["alpha"] = float(
            np.clip(new_ind["alpha"], *BOUNDS["alpha"])
        )

        new_population.append(new_ind)

    new_fitness = [evaluate(ind) for ind in new_population]

    for i in range(POP_SIZE):
        if new_fitness[i] > fitness[i]:
            population[i] = new_population[i]
            fitness[i] = new_fitness[i]

    gen_best_idx = np.argmax(fitness)
    if fitness[gen_best_idx] > best_score:
        best_score = fitness[gen_best_idx]
        best_individual = population[gen_best_idx]

    print("Best R2 so far:", best_score)

best_params = {
    "alpha": float(best_individual["alpha"])
}

best_params_path = "modelB/models/ridgeRegression/finetuned_best_params_ridge.json"

with open(best_params_path, "w") as f:
    json.dump(best_params, f, indent=2)

print("Saved best Ridge params:", best_params)

# -----------------------------
# Train final fine tuned model using best parameters
# -----------------------------

with open("modelB/models/ridgeRegression/finetuned_best_params_ridge.json", "r") as f:
    best_params = json.load(f)

finetuned_model = Ridge(
alpha=best_params["alpha"],
random_state=42
)

finetuned_model.fit(X_dev, y_dev)

joblib.dump(finetuned_model,"modelB/models/ridgeRegression/synthetic_plus_real_ridge.pkl")

# -------------------------------------------
# Load and run saved model on test data
# -------------------------------------------
loaded_model = joblib.load("modelB/models/ridgeRegression/synthetic_plus_real_ridge.pkl")


#real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")
real_test = preprocess_real(real_test, require_target=True)

X_test_raw = real_test[raw_feature_list]

X_test_enc = pd.get_dummies(X_test_raw, drop_first=True)

X_test_enc = X_test_enc.reindex(columns=SYN_FEATURE_COLS, fill_value=0)

X_test = X_test_enc
y_test = real_test["post_renovation_value"]

test_preds = loaded_model.predict(X_test)

r2 = r2_score(y_test, test_preds)
test_mape = mape(y_test, test_preds)

print("Loaded model R2 on real test:", r2)
print("Loaded model MAPE on real test:", test_mape)

# Save predictions
preds_df = pd.DataFrame({
    "y_true": y_test.values,
    "y_pred": test_preds
})

preds_path = "modelB/ridgeRegression/ridge_synthetic_test_predictions.csv"
preds_df.to_csv(preds_path, index=False)
