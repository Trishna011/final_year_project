import numpy as np
import pandas as pd
import ast
from sklearn.svm import SVR
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import json
from sklearn.model_selection import KFold
import random
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
bundle = joblib.load(
    #"/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_model.pkl"
    "modelB/models/SVR/svr_synthetic_model.pkl"
)

pipeline = bundle["model"]

scaler = pipeline.named_steps["scaler"]
svr_model = pipeline.named_steps["svr"]

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
#with open("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_best_params.json", "r") as f:
with open("modelB/models/SVR/svr_synthetic_best_params.json", "r") as f:    
    saved = json.load(f)

SYN_FEATURE_COLS = saved["feature_columns"]
SYN_MODEL_PARAMS = saved["best_params"]

old_C = svr_model.C

old_gamma = svr_model._gamma

old_epsilon = svr_model.epsilon

# -----------------------------
# Prepare train_val set for fine-tuning
# ------------------------------

#dev_df = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/real_train_val_with_predicted_reno_cost.csv")
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
print(X_dev.describe())


# =========================
# AAEO
# =========================

# Define local search bounds
# BOUNDS = {
#     "C": (old_C / 5.0, old_C * 5.0),
#     "gamma": (old_gamma / 5.0, old_gamma * 5.0),
#     "epsilon": (old_epsilon / 5.0, old_epsilon * 5.0)
# }

# # Random individual near old params
# def random_individual():
#     return {
#         "C": np.random.uniform(*BOUNDS["C"]),
#         "gamma": np.random.uniform(*BOUNDS["gamma"]),
#         "epsilon": np.random.uniform(*BOUNDS["epsilon"])
#     }

# # Evaluate with 5 fold CV
# def evaluate(individual):

#     # Extract hyperparameters from bounds
#     C = float(individual["C"])
#     gamma = float(individual["gamma"])
#     epsilon = float(individual["epsilon"])

#     kf = KFold(n_splits=5, shuffle=True, random_state=42)
#     scores = []
    
#     # Loop through each fold
#     for train_idx, val_idx in kf.split(X_dev):
        
#         # Split into training and validation sets
#         X_tr_raw = X_dev.iloc[train_idx].values
#         y_tr = y_dev.iloc[train_idx].values
#         X_va_raw = X_dev.iloc[val_idx].values
#         y_va = y_dev.iloc[val_idx].values

#         # Apply the same scaler used in synthetic training
#         X_tr = scaler.transform(X_tr_raw)
#         X_va = scaler.transform(X_va_raw)

#         # Create new SVR model with candidate hyperparameters
#         model = SVR(
#             kernel="rbf",
#             C=C,
#             gamma=gamma,
#             epsilon=epsilon
#         )

#         # Train model on training fold
#         model.fit(X_tr, y_tr)

#         # Predict on validation fold
#         preds = model.predict(X_va)

#         # Compute R2 score for this fold
#         scores.append(r2_score(y_va, preds))

#     return np.mean(scores)

# # Evolutionary Search with Early Stopping
# POP_SIZE = 8
# GENERATIONS = 50

# # stop if no improvement for this many generations
# PATIENCE = 5
# MIN_DELTA = 1e-4

# # Create initial population of random hyperparameter candidates
# population = [random_individual() for _ in range(POP_SIZE)]

# # Evaluate each candidate using 5 fold cross validation
# fitness = [evaluate(ind) for ind in population]

# # Identify the best candidate from the initial population
# best_idx = np.argmax(fitness)
# best_individual = population[best_idx]
# best_score = fitness[best_idx]

# print("Initial best R2:", best_score)

# # Counter to track how many generations pass without improvement
# no_improve_counter = 0

# # Main evolutionary loop
# for gen in range(GENERATIONS):
#     print("\nGeneration", gen + 1)

#     new_population = []

#     # Create new candidate solutions from current population
#     for i, ind in enumerate(population):

#         # With 50 percent chance, move slightly toward another candidate
#         if random.random() < 0.5:
#             partner = population[np.random.randint(POP_SIZE)]
#             new_ind = {
#                 "C": ind["C"] + np.random.uniform(-0.2, 0.2) * (partner["C"] - ind["C"]),
#                 "gamma": ind["gamma"] + np.random.uniform(-0.2, 0.2) * (partner["gamma"] - ind["gamma"]),
#                 "epsilon": ind["epsilon"] + np.random.uniform(-0.2, 0.2) * (partner["epsilon"] - ind["epsilon"])
#             }
#         # Otherwise, randomly perturb current candidate
#         else:
#             new_ind = {
#                 "C": ind["C"] + np.random.uniform(-0.1, 0.1) * ind["C"],
#                 "gamma": ind["gamma"] + np.random.uniform(-0.1, 0.1) * ind["gamma"],
#                 "epsilon": ind["epsilon"] + np.random.uniform(-0.1, 0.1) * ind["epsilon"]
#             }

#         # Ensure hyperparameters stay within allowed bounds
#         new_ind["C"] = float(np.clip(new_ind["C"], *BOUNDS["C"]))
#         new_ind["gamma"] = float(np.clip(new_ind["gamma"], *BOUNDS["gamma"]))
#         new_ind["epsilon"] = float(np.clip(new_ind["epsilon"], *BOUNDS["epsilon"]))

#         new_population.append(new_ind)

#     # Evaluate new candidates
#     new_fitness = [evaluate(ind) for ind in new_population]

#     improved = False

#     # Replace old candidates if new ones perform better
#     for i in range(POP_SIZE):
#         if new_fitness[i] > fitness[i]:
#             population[i] = new_population[i]
#             fitness[i] = new_fitness[i]

#     # Find best candidate in current generation
#     gen_best_idx = np.argmax(fitness)
#     gen_best_score = fitness[gen_best_idx]

#     # Check if global best improved enough
#     if gen_best_score > best_score + MIN_DELTA:
#         best_score = gen_best_score
#         best_individual = population[gen_best_idx]
#         no_improve_counter = 0
#         improved = True
#     else:
#         no_improve_counter += 1

#     print("Best R2 so far:", best_score)
#     print("No improvement counter:", no_improve_counter)

#     # Stop search early if no improvement for several generations
#     if no_improve_counter >= PATIENCE:
#         print("Early stopping triggered.")
#         break

# # Save best hyperparameters
# best_params = {
#     "C": float(best_individual["C"]),
#     "gamma": float(best_individual["gamma"]),
#     "epsilon": float(best_individual["epsilon"])
# }

# best_params_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/finetuned_best_params_svr.json"

# with open(best_params_path, "w") as f:
#     json.dump(best_params, f, indent=2)

# print("Saved best SVR params:", best_params)

# # --------------------------------
# # Train final SVR on full dataset
# # --------------------------------
# X_dev_scaled = scaler.transform(X_dev.values)

# final_model = SVR(
#     kernel="rbf",
#     C=best_params["C"],
#     gamma=best_params["gamma"],
#     epsilon=best_params["epsilon"]
# )

# final_model.fit(X_dev_scaled, y_dev.values)

# import joblib
# joblib.dump(final_model, "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/finetuned_svr.pkl")

# =========================
# load params and model
# =========================
params_path = "modelB/models/SVR/finetuned_best_params_svr.json"

with open(params_path, "r") as f:
    best_params = json.load(f)

C = best_params["C"]
gamma = best_params["gamma"]
epsilon = best_params["epsilon"]

print("Loaded params:", best_params)

model_path = "modelB/models/SVR/finetuned_svr.pkl"

svr_model = joblib.load(model_path)

print("Loaded model:", svr_model)

# =========================
# pred on real data and synth data
# =========================

#real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")
real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# Preprocess test data to match training schema
real_test = preprocess_real(real_test, require_target=True)

# Select raw feature columns used during training
X_test_raw = real_test[raw_feature_list]

# Align encoded test columns with synthetic training feature columns
# Add missing columns with zeros to ensure identical structure
X_test_enc = X_test_raw.reindex(columns=SYN_FEATURE_COLS)

X_test = X_test_enc
y_test = real_test["post_renovation_value"]

# Scale features using same scaler fitted during training
X_test_scaled = scaler.transform(X_test.values)

# Generate predictions
test_preds = svr_model.predict(X_test_scaled)

r2 = r2_score(y_test, test_preds)
test_mape = mape(y_test, test_preds)
rmse = np.sqrt(mean_squared_error(y_test, test_preds))
mae = mean_absolute_error(y_test, test_preds)

print("Loaded model R2 on real test:", r2)
print("Loaded model MAPE on real test:", test_mape)
print("Loaded model RMSE on real test:", rmse)
print("Loaded model MAE on real test:", mae)

# Save predictions
# preds_df = pd.DataFrame({
#     "y_true": y_test.values,
#     "y_pred": test_preds
# })

# preds_path = "modelB/SVR/svr_finetuned_synthetic_predictions.csv"
# preds_df.to_csv(preds_path, index=False)