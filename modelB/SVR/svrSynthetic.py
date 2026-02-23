import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score
import joblib
import json
from sklearn.model_selection import ParameterGrid, KFold, GridSearchCV
from sklearn.pipeline import Pipeline


def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan

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

        # structural_change naming consistency - needed here as you didn't save synth feature cols
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

# -------------------
# load synthetic data
# -------------------
#train_exp = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_train_expanded.csv")
train_exp = pd.read_csv("processed_data/synthetic_train_expanded.csv")
#val_exp = pd.read_csv("/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/synthetic_val_expanded.csv")
val_exp = pd.read_csv("processed_data/synthetic_val_expanded.csv")
test_exp = pd.read_csv("processed_data/synthetic_test_expanded.csv")

# ---------------------------------
# DEFINE TARGET AND FEATURE COLUMNS
# ---------------------------------

# Target variable we want to predict
target = "post_renovation_value"

# Feature columns used as model inputs
# These must match exactly during training, validation, and testing
features = [
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

# ---------------------------------
# CLEAN DATA
# ---------------------------------

# Remove rows where target is missing
train_exp = train_exp.dropna(subset=[target])
val_exp = val_exp.dropna(subset=[target])

# Separate features (X) and target (y)
X_train = train_exp[features]
y_train = train_exp[target]

X_val = val_exp[features]
y_val = val_exp[target]


# ---------------------------------
# BUILD PIPELINE
# ---------------------------------

pipeline = Pipeline([
    # Standardize features: (x - mean) / std
    # Important for SVR since it is sensitive to feature scale
    ("scaler", StandardScaler()),
    ("svr", SVR(kernel="rbf"))
])

# ---------------------------------
# PARAMETER GRID
# ---------------------------------

# param_grid = {
# "svr__C": [1000, 10000, 50000, 100000],
# "svr__epsilon": [ 0.005,0.01,0.05,0.1,0.2,0.5],
# "svr__gamma": ["scale", 1, 0.1, 0.01, 0.001, 0.0001]
# }

# # ---------------------------------
# # Cross validation grid search
# # ---------------------------------

# best_r2 = -np.inf
# best_params = None
# best_model = None

# # 5-fold cross-validation
# kf = KFold(n_splits=5, shuffle=True, random_state=42)

# grid = GridSearchCV(
#     pipeline,
#     param_grid,
#     cv=5,
#     scoring="r2",
#     n_jobs=8
# )

# # Train model across all hyperparameter combinations
# grid.fit(X_train, y_train)

# # ---------------------------------
# # Results
# # ---------------------------------
# print("Best CV R2:", grid.best_score_)
# print("Best params:", grid.best_params_)

# best_model = grid.best_estimator_

# # -------------------------
# # Save model
# # -------------------------

# model_bundle = {
# "model": best_model
# }

# #model_path = "modelB/models/SVR/svr_synthetic_model.pkl"
# model_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_model.pkl"
# joblib.dump(model_bundle, model_path)

# # -------------------------
# # SAVE PARAMETERS + FEATURE COLUMNS
# # -------------------------

# #params_path = "modelB/models/SVR/svr_synthetic_best_params.json"
# params_path = "/mnt/iusers01/fse-ugpgt01/compsci01/s57786tm/project/svr_synthetic_best_params.json"

# params_to_save = {
# "best_params": grid.best_params_,
# "feature_columns": list(X_train.columns)
# }

# with open(params_path, "w") as f:
#     json.dump(params_to_save, f, indent=2)

# -------------------------
# # Load model + params
# -------------------------
model_path = "modelB/models/SVR/svr_synthetic_model.pkl"
params_path = "modelB/models/SVR/svr_synthetic_best_params.json"

model_bundle = joblib.load(model_path)
model = model_bundle["model"]

with open(params_path, "r") as f:
    params_data = json.load(f)

feature_columns = params_data["feature_columns"]

# -------------------------
# test on synth data
# -------------------------
# target = "post_renovation_value"

# # Drop missing targets
# test_exp = test_exp.dropna(subset=[target])

# # # Predict (row level)
# X_test = test_exp[feature_columns]
# y_test = test_exp[target].values

# y_pred = model.predict(X_test)

# # # Aggregate to property level
# test_df = pd.DataFrame({
#     "source_row": test_exp["source_row"].values,
#     "y_true": y_test,
#     "y_pred": y_pred
# })

# prop_level = test_df.groupby("source_row", as_index=False).agg(
#     y_true=("y_true", "first"),
#     y_pred=("y_pred", "mean")
# )

# # Metrics (property level)
# prop_r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
# prop_mape = mape(prop_level["y_true"], prop_level["y_pred"])

# print("Property-level TEST R2:", prop_r2)
# print("Property-level TEST MAPE:", prop_mape)

# -----------------------
# Preds real data
# -----------------------
real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# Preprocess features
real_df = preprocess_real(real_df)

# Ground truth (post renovation value)
y_true = real_df["price"]

# Ensure feature alignment
X_real = real_df[features]

real_preds = model.predict(X_real)

real_r2 = r2_score(y_true, real_preds)
real_mape = mape(y_true, real_preds)

print("Random Forest R2 (real test):", real_r2)
print("Random Forest MAPE (real test):", real_mape)


# -------------------------
# SAVE PREDICTIONS FOR WILCOXON
# -------------------------
svr_preds_path = "modelB/SVR/svr_train_real_preds.csv"

pred_df = pd.DataFrame({
    "source_row": real_df.index,
    "y_true": y_true.values,
    "y_pred": real_preds
})

# pred_df = pd.DataFrame({
#     "source_row": prop_level["y_true"].index,
#     "y_true": prop_level["y_true"].values,
#     "y_pred": prop_level["y_pred"].values
# })

pred_df.to_csv(svr_preds_path, index=False)

