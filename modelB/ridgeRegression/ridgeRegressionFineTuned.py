import numpy as np
import pandas as pd
import ast
from sklearn.linear_model import SGDRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import KFold
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
syn_model = joblib.load(
"modelB/models/ridgeRegression/ridge_synthetic_model.pkl"
)

scaler = syn_model.named_steps["scaler"]
ridge_model = syn_model.named_steps["ridge"]

w_syn = ridge_model.coef_
b_syn = ridge_model.intercept_

# -----------------------------
# Load saved feature schema and model parameters
# Ensures real data matches synthetic training structure
# -----------------------------
with open("modelB/models/ridgeRegression/ridge_synthetic_best_params.json", "r") as f:
    saved = json.load(f)

SYN_FEATURE_COLS = saved["feature_columns"]
SYN_MODEL_PARAMS = saved["ridge_params"]

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


# -----------------------------
# Tune Ridge with AAEO
# -----------------------------
# BOUNDS = {
#     "alpha": (1e-6, 10.0),
#     "eta0": (1e-5, 0.1)
# }

# # Random parameter generator
# def random_individual():
#     return {
#     "alpha": 10 ** np.random.uniform(-6, 1),
#     "eta0": 10 ** np.random.uniform(-5, -1)
# }

# # Evaluate parameter set using 5 fold CV
# def evaluate(individual):

#     # Extract hyperparameters from candidate solution
#     # alpha controls L2 regularization strength
#     # eta0 controls learning rate
#     alpha = float(individual["alpha"])
#     eta0 = float(individual["eta0"])

#     # Create 5 fold split
#     # Data is shuffled for robustness
#     kf = KFold(n_splits=5, shuffle=True, random_state=42)
#     scores = []

#     # Loop over each train and validation split
#     for train_idx, val_idx in kf.split(X_dev):

#         # Split raw features and targets
#         X_tr_raw = X_dev.iloc[train_idx].values
#         y_tr = y_dev.iloc[train_idx].values
#         X_va_raw = X_dev.iloc[val_idx].values
#         y_va = y_dev.iloc[val_idx].values

#         # Scale features using pre fitted scaler
#         # Important to apply same scaling to train and validatio
#         X_tr = scaler.transform(X_tr_raw)
#         X_va = scaler.transform(X_va_raw)

#         # Create SGD regression model
#         # max_iter=1 and warm_start=True allow manual control of training steps
#         model = SGDRegressor(
#             penalty="l2",
#             alpha=alpha,
#             learning_rate="constant",
#             eta0=eta0,
#             max_iter=1,
#             warm_start=True,
#             random_state=42
#         )

#         # Initialize model with one small batch
#         # This creates internal structures
#         model.partial_fit(X_tr[:1], y_tr[:1])

#         # Replace weights with pretrained synthetic weights
#         # This starts fine tuning from synthetic solution
#         model.coef_ = w_syn.copy()
#         model.intercept_ = np.array([b_syn])

#         # Fine tune on real training fold
#         # Run 10 passes over training data
#         for _ in range(10):
#             model.partial_fit(X_tr, y_tr)

#         # Predict on validation fold
#         preds = model.predict(X_va)
        
#         # Compute R2 score and store
#         scores.append(r2_score(y_va, preds))

#     return np.mean(scores)



# # -----------------------------
# # Evolutionary Search
# # -----------------------------

# # Number of candidate solutions per generation
# POP_SIZE = 8

# # Number of optimization rounds
# GENERATIONS = 10

# # Create initial population
# # Each individual is a random set of hyperparameters
# population = [random_individual() for _ in range(POP_SIZE)]

# # Evaluate each individual using 5 fold CV
# # Fitness = average R2 score
# fitness = [evaluate(ind) for ind in population]

# # Identify best individual from initial population
# best_idx = np.argmax(fitness)
# best_individual = population[best_idx]
# best_score = fitness[best_idx]

# print("Initial best R2:", best_score)

# # Evolution loop
# for gen in range(GENERATIONS):
#     print("\nGeneration", gen + 1)

#     # Store newly created individuals
#     new_population = []

#     # Create new candidate for each current individual
#     for i, ind in enumerate(population):
        
#         # With 50 percent probability:
#         # Combine current individual with another random partner
#         # Move slightly toward partner in parameter space
#         if random.random() < 0.5:
#             partner = population[np.random.randint(POP_SIZE)]
#             new_ind = {
#             "alpha": ind["alpha"] + np.random.uniform(-0.2, 0.2) * (partner["alpha"] - ind["alpha"]),
#             "eta0": ind["eta0"] + np.random.uniform(-0.2, 0.2) * (partner["eta0"] - ind["eta0"])
#             }
        
#         # Otherwise:
#         # Slightly perturb parameters randomly
#         else:
#             new_ind = {
#             "alpha": ind["alpha"] + np.random.uniform(-0.1, 0.1),
#             "eta0": ind["eta0"] + np.random.uniform(-0.1, 0.1)
#             }

#         # Keep parameters within allowed bounds
#         # Prevent invalid values
#         new_ind["alpha"] = float(np.clip(new_ind["alpha"], *BOUNDS["alpha"]))
#         new_ind["eta0"] = float(np.clip(new_ind["eta0"], *BOUNDS["eta0"]))
        
#         new_population.append(new_ind)

#     # Evaluate new candidates
#     new_fitness = [evaluate(ind) for ind in new_population]

#     # Replacement
#     # If new candidate performs better than current one,
#     # replace the old individual
#     for i in range(POP_SIZE):
#         if new_fitness[i] > fitness[i]:
#             population[i] = new_population[i]
#             fitness[i] = new_fitness[i]

#     # Track global best solution
#     gen_best_idx = np.argmax(fitness)
#     if fitness[gen_best_idx] > best_score:
#         best_score = fitness[gen_best_idx]
#         best_individual = population[gen_best_idx]

#     print("Best R2 so far:", best_score)

# # Save best hyperparameters found
# best_params = {
#     "alpha": float(best_individual["alpha"]),
#     "eta0": float(best_individual["eta0"])
# }

# best_params_path = "modelB/models/ridgeRegression/finetuned_best_params_ridge.json"

# with open(best_params_path, "w") as f:
#     json.dump(best_params, f, indent=2)

# print("Saved best Ridge params:", best_params)

# # -----------------------------
# # Train final fine tuned model using best parameters
# # -----------------------------

# with open("modelB/models/ridgeRegression/finetuned_best_params_ridge.json", "r") as f:
#     best_params = json.load(f)

# # Create final SGD regression model using tuned hyperparameters
# # L2 penalty makes this equivalent to ridge regression
# final_model = SGDRegressor(
#     penalty="l2",
#     alpha=best_params["alpha"],
#     learning_rate="constant",
#     eta0=best_params["eta0"],
#     max_iter=1,
#     warm_start=True,
#     random_state=42
# )

# # Scale full development dataset using training scaler
# X_dev_scaled = scaler.transform(X_dev.values)

# # Initialize model internal structure with one sample
# # Required before manually setting coefficients
# final_model.partial_fit(X_dev_scaled[:1], y_dev.values[:1])

# # Replace weights with pretrained synthetic weights
# # Start fine tuning from synthetic solution
# final_model.coef_ = w_syn.copy()
# final_model.intercept_ = np.array([b_syn])

# # Fine tune on full real dataset
# # Run 20 passes over the data
# for _ in range(20):
#     final_model.partial_fit(X_dev_scaled, y_dev.values)

# joblib.dump(final_model, "modelB/models/ridgeRegression/synthetic_plus_real_sgd.pkl")

# -------------------------------------------
# Load and run saved model on test data
# -------------------------------------------
with open("modelB/models/ridgeRegression/finetuned_best_params_ridge.json", "r") as f:
    best_params = json.load(f)

loaded_model = joblib.load("modelB/models/ridgeRegression/synthetic_plus_real_sgd.pkl")


real_test = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")
#real_test = pd.read_csv("processed_data/synthetic_test_expanded.csv")

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
test_preds = loaded_model.predict(X_test_scaled)

r2 = r2_score(y_test, test_preds)
test_mape = mape(y_test, test_preds)
rmse = np.sqrt(mean_squared_error(y_test, test_preds))
mae = mean_absolute_error(y_test, test_preds)

print("Loaded model R2 on real test:", r2)
print("Loaded model MAPE on real test:", test_mape)
print("Loaded model RMSE on real test:", rmse)
print("Loaded model MAE on real test:", mae)

# Save predictions
preds_df = pd.DataFrame({
    "y_true": y_test.values,
    "y_pred": test_preds
})

# preds_path = "modelB/ridgeRegression/ridge_finetuned_synthetic_predictions.csv"
# preds_df.to_csv(preds_path, index=False)