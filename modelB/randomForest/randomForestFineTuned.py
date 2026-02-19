import numpy as np
import pandas as pd
import ast
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor
import json
import random
import os
import joblib

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
            columns=["type_of_renovation", "type_of_renovation_parsed", "Location", "id", "extended_rooms"],
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
syn_model = joblib.load("modelB/models/randomForest/randomforest_synthetic_model.pkl")

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
with open("modelB/models/randomForest/randomforest_synthetic_best_params.json", "r") as f:
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


#-----------------------------
# tune randomForest with AAEO
#-----------------------------
BOUNDS = {
    "max_features": (0.001, 0.04),
    "max_depth": (4, 8),
    "min_samples_leaf": (1, 15),
    "n_estimators": (150, 600)
}

# Random parameter generator
def random_individual():
    return {
        "max_features": np.random.uniform(*BOUNDS["max_features"]),
        "max_depth": np.random.randint(*BOUNDS["max_depth"] + (1,)),
        "min_samples_leaf": np.random.uniform(*BOUNDS["min_samples_leaf"]),
        "n_estimators": np.random.randint(*BOUNDS["n_estimators"] + (1,))
    }

# Evaluate parameter set by doing k-fold cross validation 
def evaluate(individual):
    clean_params = {}
    
    clean_params = {
        "n_estimators": int(individual["n_estimators"]),
        "max_depth": int(individual["max_depth"]),
        "min_samples_leaf": int(individual["min_samples_leaf"]),
        "max_features": float(individual["max_features"]),
    }   
    
    # data set split into 5 folds 
    # each fold is used once as validation while the other 4 form the training set
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    fold_scores = []

    for train_idx, val_idx in kf.split(X_dev):
        
        X_tr = X_dev.iloc[train_idx]
        y_tr = y_dev.iloc[train_idx]

        X_va = X_dev.iloc[val_idx]
        y_va = y_dev.iloc[val_idx]

        # 1. Load fresh synthetic model
        base_model = joblib.load(
            "modelB/models/randomForest/randomforest_synthetic_model.pkl"
        )

        # 2. Enable warm start
        base_model.set_params(warm_start=True)


        # 3. Apply structural params for NEW trees
        base_model.set_params(
            max_depth=clean_params["max_depth"],
            min_samples_leaf=clean_params["min_samples_leaf"],
            max_features=clean_params["max_features"],
        )

        # 4. Increase number of trees incrementially to mimic early stopping
        original_trees = base_model.n_estimators
        max_additional = clean_params["max_additional_trees"]

        step = 50
        best_score = -np.inf
        current_trees = original_trees

        while current_trees < original_trees + max_additional:
            current_trees += step
            base_model.set_params(n_estimators=current_trees)
            base_model.fit(X_tr, y_tr)

            preds = base_model.predict(X_va)
            score = r2_score(y_va, preds)

            if score > best_score:
                best_score = score
            else:
                break
        
        fold_scores.append(best_score)

    return np.mean(fold_scores)

# -----------------------------
# EVOLUTIONARY SEARCH
# -----------------------------
POP_SIZE = 8
GENERATIONS = 10

# Randomly generate 8 different parameter sets from BOUNDS
population = [random_individual() for _ in range(POP_SIZE)]

# Train a model for each parameter set and compute its R2 on validation data. That R2 is the fitness score.
fitness = [evaluate(ind) for ind in population]

# Find which candidate performs best.
best_idx = np.argmax(fitness)
best_individual = population[best_idx]
best_score = fitness[best_idx]

print("Initial best R2:", best_score)

for gen in range(GENERATIONS):
    print(f"\nGeneration {gen + 1}")

    # For each generation:
    # Create new candidates
    new_population = []
    
    for i, ind in enumerate(population):

        # For each current individual:
        # With 50 percent probability:
        if random.random() < 0.5:

            # You combine it with another random candidate.
            partner = population[np.random.randint(POP_SIZE)]

            # new_value = current + random factor × difference from partner
            # This is exploration using direction between two solutions.
            new_ind = {
                k: ind[k] + np.random.uniform(-0.2, 0.2) * (partner[k] - ind[k])
                for k in ind
            }
        # Otherwise slightly perturb each parameter randomly.    
        else:
            new_ind = {
                k: ind[k] + np.random.uniform(-0.1, 0.1)
                for k in ind
            }

        # Force each parameter to remain within allowed limits using np.clip.
        # This prevents invalid values.
        new_ind["n_estimators"] = int(
            np.clip(new_ind["n_estimators"], *BOUNDS["n_estimators"])
        )

        new_ind["max_depth"] = int(
            np.clip(new_ind["max_depth"], *BOUNDS["max_depth"])
        )

        new_ind["min_samples_leaf"] = int(
            np.clip(new_ind["min_samples_leaf"], *BOUNDS["min_samples_leaf"])
        )

        new_ind["max_features"] = float(
            np.clip(new_ind["max_features"], *BOUNDS["max_features"])
        )

        new_population.append(new_ind)

    # Train a model for each new parameter set and compute R2.
    new_fitness = [evaluate(ind) for ind in new_population]

    # Replace old population with new population if fitness improves.
    for i in range(POP_SIZE):
        if new_fitness[i] > fitness[i]:
            population[i] = new_population[i]
            fitness[i] = new_fitness[i]

    # Track best performing candidate across all generations.
    gen_best_idx = np.argmax(fitness)
    if fitness[gen_best_idx] > best_score:
        best_score = fitness[gen_best_idx]
        best_individual = population[gen_best_idx]

    print("Best R2 so far:", best_score)

    # Save best parameters found
    best_params = {
        "max_features": float(best_individual["max_features"]),
        "max_depth": int(best_individual["max_depth"]),
        "min_samples_leaf": int(best_individual["min_samples_leaf"]),
        "n_estimators": int(best_individual["n_estimators"])
        }
    
best_params_path = "modelB/models/lightGBM/finetuned_best_params_lightGBM_AAEO.json"
with open(best_params_path, "w") as f:
    json.dump(best_params, f, indent=2)

# # -----------------------------
# # Train final fine tuned model using best parameters
# # -----------------------------

# with open("modelB/models/lightGBM/finetuned_best_params_lightGBM_AAEO.json", "r") as f:
#     best_params = json.load(f)


# joblib.dump(finetuned_model, "modelB/models/randomForest/synthetic_plus_real_rf.pkl")


# # -------------------------------------------
# # Load and run saved model on test data
# # -------------------------------------------
# loaded_model = joblib.load("modelB/models/randomForest/synthetic_plus_real_rf.pkl")


# #real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
# real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")
# real_test = preprocess_real(real_test, require_target=True)

# X_test_raw = real_test[raw_feature_list]

# X_test_enc = pd.get_dummies(X_test_raw, drop_first=True)

# X_test_enc = X_test_enc.reindex(columns=SYN_FEATURE_COLS, fill_value=0)

# X_test = X_test_enc
# y_test = real_test["post_renovation_value"]

# test_preds = loaded_model.predict(X_test)

# r2 = r2_score(y_test, test_preds)
# test_mape = mape(y_test, test_preds)

# print("Loaded model R2 on real test:", r2)
# print("Loaded model MAPE on real test:", test_mape)

# # Save predictions
# preds_df = pd.DataFrame({
#     "y_true": y_test.values,
#     "y_pred": test_preds
# })

# preds_path = "modelB/lightGBM/lightgbm_synthetic_test_predictions.csv"
# preds_df.to_csv(preds_path, index=False)