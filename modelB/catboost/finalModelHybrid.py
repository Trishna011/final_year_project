import json
import pandas as pd
import numpy as np
import ast
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import r2_score
import random
from sklearn.model_selection import KFold

# -----------------------------
# helpers
# -----------------------------
def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


# Normalize material text into consistent format
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

# Normalize renovation tokens
def normalize_token(x):
    return " ".join(x.lower().strip().split())

# Parse renovation type column into list format
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
    return df


# -----------------------------
# load pretrained synthetic model
# -----------------------------
syn_model = CatBoostRegressor()
syn_model.load_model("modelB/models/synthetic_catboost_best_model.cbm")

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
with open("modelB/models/synthetic_catboost_best_params.json", "r") as f:
    saved = json.load(f)

SYN_FEATURE_COLS = saved["feature_columns"]
SYN_MODEL_PARAMS = saved["model_params"]

# -----------------------------
# prepare validation set for fine tuning
# -----------------------------
real_val = pd.read_csv("processed_data/real_val_with_predicted_reno_cost.csv")
real_val = preprocess_real(real_val, require_target=True)

# Use real price as target as price is the same as post renovation value
real_val["post_renovation_value"] = real_val["price"]

# Ensure all required synthetic features exist
for col in set(SYN_FEATURE_COLS) - set(real_val.columns):
    real_val[col] = 0

X_val = real_val[SYN_FEATURE_COLS]
y_val = real_val["post_renovation_value"]

val_pool = Pool(
    X_val,
    y_val,
    cat_features=[X_val.columns.get_loc("unit_type")]
)

# -----------------------------
# Prepare real training set for fine tuning
# -----------------------------
real_train = pd.read_csv("processed_data/real_with_predicted_reno_cost.csv")
real_train = preprocess_real(real_train, require_target=True)

real_train["post_renovation_value"] = real_train["price"]

for col in set(SYN_FEATURE_COLS) - set(real_train.columns):
    real_train[col] = 0

X_train = real_train[SYN_FEATURE_COLS]
y_train = real_train["post_renovation_value"]

train_pool = Pool(
    X_train,
    y_train,
    cat_features=[X_train.columns.get_loc("unit_type")]
)

# -----------------------------
# Combine real training and validation data for cross validation during tuning
# ------------------------------
dev_df = pd.concat([real_train, real_val], ignore_index=True)
dev_df["post_renovation_value"] = dev_df["price"]

for col in set(SYN_FEATURE_COLS) - set(dev_df.columns):
    dev_df[col] = 0

X_dev = dev_df[SYN_FEATURE_COLS]
y_dev = dev_df["post_renovation_value"]

# -----------------------------
# tune with AAEO
# -----------------------------
BOUNDS = {
    "learning_rate": (0.001, 0.04),
    "depth": (4, 8),
    "l2_leaf_reg": (1, 15),
    "iterations": (150, 600)
}

# Random parameter generator
def random_individual():
    return {
        "learning_rate": np.random.uniform(*BOUNDS["learning_rate"]),
        "depth": np.random.randint(*BOUNDS["depth"] + (1,)),
        "l2_leaf_reg": np.random.uniform(*BOUNDS["l2_leaf_reg"]),
        "iterations": np.random.randint(*BOUNDS["iterations"] + (1,))
    }

# Evaluate parameter set by doing k-fold cross validation 
def evaluate(individual):
    clean_params = {}
    for k, v in individual.items():
        if k in ["depth", "iterations"]:
            clean_params[k] = int(v)
        else:
            clean_params[k] = float(v)

    # data set split into 5 folds 
    # each fold is used once as validation while the other 4 form the training set
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    fold_scores = []

    for train_idx, val_idx in kf.split(X_dev):

        X_tr = X_dev.iloc[train_idx]
        y_tr = y_dev.iloc[train_idx]

        X_va = X_dev.iloc[val_idx]
        y_va = y_dev.iloc[val_idx]

        # Training inside each fold
        # Fine tunes on synthetic model 
        train_pool = Pool(
            X_tr,
            y_tr,
            cat_features=[X_tr.columns.get_loc("unit_type")]
        )

        val_pool = Pool(
            X_va,
            y_va,
            cat_features=[X_va.columns.get_loc("unit_type")]
        )

        model = CatBoostRegressor(
            loss_function="RMSE",
            eval_metric="R2",
            random_seed=42,
            verbose=False,
            **clean_params
        )

        #Early stopping used bc 
        # if validation score does not improve for 100 consecutive rounds:
        # Then training stop early to prevent overfitting and save time
        model.fit(
            train_pool,
            eval_set=val_pool,
            init_model=syn_model,
            use_best_model=True,
            early_stopping_rounds=100
        )

        # Computing R2 for this fold
        preds = model.predict(val_pool)
        fold_scores.append(r2_score(y_va, preds))

    return np.mean(fold_scores)

# Small evolutionary optimization loop to tune CatBoost hyperparameters.
# Find the combination of learning_rate, depth, l2_leaf_reg, and iterations that maximizes R2 on the validation set.

# Create 8 candidate parameter sets per generation.
POP_SIZE = 8

#Take the current 8 parameter sets.
#Slightly modify them.
#Test the new ones.
#Keep the better ones.
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
        new_ind["learning_rate"] = float(
            np.clip(new_ind["learning_rate"], *BOUNDS["learning_rate"])
        )

        new_ind["depth"] = int(
            np.clip(new_ind["depth"], *BOUNDS["depth"])
        )

        new_ind["l2_leaf_reg"] = float(
            np.clip(new_ind["l2_leaf_reg"], *BOUNDS["l2_leaf_reg"])
        )

        new_ind["iterations"] = int(
            np.clip(new_ind["iterations"], *BOUNDS["iterations"])
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
        "learning_rate": float(best_individual["learning_rate"]),
        "depth": int(best_individual["depth"]),
        "l2_leaf_reg": float(best_individual["l2_leaf_reg"]),
        "iterations": int(best_individual["iterations"])
        }

best_params_path = "modelB/models/finetuned_best_params_AAEO.json"
with open(best_params_path, "w") as f:
    json.dump(best_params, f, indent=2)



# -----------------------------
# Train final fine tuned model using best parameters
# -----------------------------

with open("modelB/models/finetuned_best_params_AAEO.json", "r") as f:
    best_params = json.load(f)


finetuned_model = CatBoostRegressor(
    loss_function="RMSE",
    eval_metric="R2",
    random_seed=42,
    verbose=200,
    model_shrink_rate=0.1,
    **best_params
)

final_pool = Pool(
    X_dev,
    y_dev,
    cat_features=[X_dev.columns.get_loc("unit_type")]
)

finetuned_model.fit(
    final_pool,
    init_model=syn_model
)



#finetuned_model.save_model("modelB/models/synthetic_plus_real_catboost_model.cbm")


# -------------------------------------------
# Load and run saved model on test data
# -------------------------------------------
loaded_model = CatBoostRegressor()
loaded_model.load_model("modelB/models/synthetic_plus_real_catboost_model.cbm")


real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
real_test = preprocess_real(real_test, require_target=True)

real_test["post_renovation_value"] = real_test["price"]

for col in set(SYN_FEATURE_COLS) - set(real_test.columns):
    real_test[col] = 0

X_test = real_test[SYN_FEATURE_COLS]
y_test = real_test["post_renovation_value"]

train_pool = Pool(
    X_test,
    y_test,
    cat_features=[X_test.columns.get_loc("unit_type")]
)

test_preds = loaded_model.predict(train_pool)

r2 = r2_score(y_test, test_preds)
test_mape = mape(y_test, test_preds)

print("Loaded model R2 on real test:", r2)
print("Loaded model MAPE on real test:", test_mape)


