import numpy as np
import pandas as pd
import ast
import json
from sklearn.metrics import r2_score
from lightgbm import early_stopping, log_evaluation, LGBMRegressor, Booster
import joblib
import random
from sklearn.model_selection import KFold


# -----------------------------
# Helpers
# -----------------------------
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
# Convert renovation type column into a list.
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

        # Create multi label binary encoding for renovation types
        fixed_types = {
            "bathroom": "bathroom",
            "bedroom": "bedroom",
            "kitchen": "kitchen",
            "living room": "living_room",
            "other/custom": "other_custom",
            "full renovation": "full_renovation"
        }

        # initialize all to 0
        for suffix in fixed_types.values():
            df[f"reno_{suffix}"] = 0

        # set 1 if renovation type exists
        for key, suffix in fixed_types.items():
            df[f"reno_{suffix}"] = df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))


        # Drop unused columns
        df = df.drop(
            columns=["type_of_renovation", "type_of_renovation_parsed", "Location", "id", "extended_rooms"],
            errors="ignore"
        )

        df["post_renovation_value"] = df["price"]

        # structural_change naming consistency
        if "structural_changes" in df.columns:
            df["structural_change"] = df["structural_changes"].astype(int)


    else:
        # Ensure correct types
        df["material_grade"] = df["material_grade"].astype(float)

        df = df.drop(
            columns=["source_row"],
            errors="ignore"
        )
    return df


# -----------------------------
# Load pretrained synthetic model
# -----------------------------
syn_model = joblib.load("modelB/models/lightGBM/lightgbm_synthetic_model.pkl")

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
with open("modelB/models/lightGBM/lightgbm_synthetic_best_params.json", "r") as f:
    saved = json.load(f)

SYN_FEATURE_COLS = saved["feature_columns"]
SYN_MODEL_PARAMS = saved["model_params"]

# -----------------------------
# Prepare real dev set
# -----------------------------
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
    "structural_change",
    "reno_bathroom",
    "reno_bedroom",
    "reno_kitchen",
    "reno_living_room",
    "reno_other_custom",
    "reno_full_renovation"
]

X_dev_raw = dev_df[raw_feature_list]
X_dev_enc = pd.get_dummies(X_dev_raw, drop_first=True)
X_dev_enc = X_dev_enc.reindex(columns=SYN_FEATURE_COLS)

X_dev = X_dev_enc
y_dev = dev_df["post_renovation_value"]

# -----------------------------
# AAEO-style tuning for LightGBM
# -----------------------------
# BOUNDS = {
#     "learning_rate": (0.001, 0.04),
#     "max_depth": (4, 8),
#     "num_leaves": (20, 80),
#     "n_estimators": (150, 600)
# }

# def random_individual():
#     return {
#         "learning_rate": np.random.uniform(*BOUNDS["learning_rate"]),
#         "max_depth": np.random.randint(BOUNDS["max_depth"][0], BOUNDS["max_depth"][1] + 1),
#         "num_leaves": np.random.randint(BOUNDS["num_leaves"][0], BOUNDS["num_leaves"][1] + 1),
#         "n_estimators": np.random.randint(BOUNDS["n_estimators"][0], BOUNDS["n_estimators"][1] + 1)
#     }

# def evaluate(individual):

#     clean_params = {
#         "learning_rate": float(individual["learning_rate"]),
#         "max_depth": int(individual["max_depth"]),
#         "num_leaves": int(individual["num_leaves"]),
#         "n_estimators": int(individual["n_estimators"]),
#         "objective": "regression",
#         "random_state": 42
#     }

#     kf = KFold(n_splits=5, shuffle=True, random_state=42)
#     fold_scores = []

#     for train_idx, val_idx in kf.split(X_dev):

#         X_tr = X_dev.iloc[train_idx]
#         y_tr = y_dev.iloc[train_idx]

#         X_va = X_dev.iloc[val_idx]
#         y_va = y_dev.iloc[val_idx]

#         model = LGBMRegressor(**clean_params)

#         model.fit(
#             X_tr,
#             y_tr,
#             eval_set=[(X_va, y_va)],
#             eval_metric="rmse",
#             init_model=syn_model,
#             callbacks=[
#                 early_stopping(100),
#                 log_evaluation(0)
#             ]
#         )

#         preds = model.predict(X_va)
#         fold_scores.append(r2_score(y_va, preds))

#     return np.mean(fold_scores)

# POP_SIZE = 8
# GENERATIONS = 10

# population = [random_individual() for _ in range(POP_SIZE)]
# fitness = [evaluate(ind) for ind in population]

# best_idx = np.argmax(fitness)
# best_individual = population[best_idx]
# best_score = fitness[best_idx]

# print("Initial best R2:", best_score)

# for gen in range(GENERATIONS):

#     print("Generation", gen + 1)
#     new_population = []

#     for ind in population:

#         if random.random() < 0.5:
#             partner = population[np.random.randint(POP_SIZE)]
#             new_ind = {
#                 k: ind[k] + np.random.uniform(-0.2, 0.2) * (partner[k] - ind[k])
#                 for k in ind
#             }
#         else:
#             new_ind = {
#                 k: ind[k] + np.random.uniform(-0.1, 0.1)
#                 for k in ind
#             }

#         new_ind["learning_rate"] = float(
#             np.clip(new_ind["learning_rate"], *BOUNDS["learning_rate"])
#         )

#         new_ind["max_depth"] = int(
#             np.clip(new_ind["max_depth"], *BOUNDS["max_depth"])
#         )

#         new_ind["num_leaves"] = int(
#             np.clip(new_ind["num_leaves"], *BOUNDS["num_leaves"])
#         )

#         new_ind["n_estimators"] = int(
#             np.clip(new_ind["n_estimators"], *BOUNDS["n_estimators"])
#         )

#         new_population.append(new_ind)

#     new_fitness = [evaluate(ind) for ind in new_population]

#     for i in range(POP_SIZE):
#         if new_fitness[i] > fitness[i]:
#             population[i] = new_population[i]
#             fitness[i] = new_fitness[i]

#     gen_best_idx = np.argmax(fitness)
#     if fitness[gen_best_idx] > best_score:
#         best_score = fitness[gen_best_idx]
#         best_individual = population[gen_best_idx]

#     print("Best R2 so far:", best_score)

# best_params = {
#     "learning_rate": float(best_individual["learning_rate"]),
#     "max_depth": int(best_individual["max_depth"]),
#     "num_leaves": int(best_individual["num_leaves"]),
#     "n_estimators": int(best_individual["n_estimators"])
# }

# with open("modelB/models/lightGBM/finetuned_best_params_AAEO.json", "w") as f:
#     json.dump(best_params, f, indent=2)

# # -------------------------------------------------------
# # Train final fine tuned LightGBM model
# # -------------------------------------------------------
# final_model = LGBMRegressor(
#     objective="regression",
#     random_state=42,
#     **best_params
# )

# final_model.fit(
#     X_dev,
#     y_dev,
#     init_model=syn_model
# )

# final_model.booster_.save_model(
#     "modelB/models/lightGBM/synthetic_plus_real_lightgbm_model.txt"
# )

# -------------------------------------------------------
# Load and evaluate on test data
# -------------------------------------------------------
loaded_booster = Booster(
    model_file="modelB/models/lightGBM/synthetic_plus_real_lightgbm_model.txt"
)

real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")
#real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
real_test = preprocess_real(real_test, require_target=True)

X_test_raw = real_test[raw_feature_list]
X_test_enc = pd.get_dummies(X_test_raw, drop_first=True)
X_test_enc = X_test_enc.reindex(columns=SYN_FEATURE_COLS)

X_test = X_test_enc
y_test = real_test["post_renovation_value"]

test_preds = loaded_booster.predict(X_test)

r2 = r2_score(y_test, test_preds)


test_mape = mape(y_test, test_preds)

print("Loaded LightGBM R2 on test:", r2)
print("Loaded LightGBM MAPE on test:", test_mape)

preds_df = pd.DataFrame({
    "y_true": y_test.values,
    "y_pred": test_preds
})

preds_df.to_csv(
    "modelB/lightGBM/lightgbm_finetuned_synthetic_predictions.csv",
    index=False
)