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

def preprocess_real_data(df):
    df = df.copy()

    # --------------------------------------------------
    # 1. Fix column names
    # --------------------------------------------------
    
    df["structural_change"] = df["structural_changes"]

    # --------------------------------------------------
    # 2. Encode material_grade to numeric
    # MUST match synthetic encoding if used during training
    # Adjust mapping if different
    # --------------------------------------------------
    material_map = {
        "mid-range": 1,
        "high-end": 2,
        "low-end": 0
    }

    df["material_grade"] = df["material_grade"].map(material_map).fillna(1)

    # --------------------------------------------------
    # 4. Create renovation flags from type_of_renovation
    # --------------------------------------------------
    def parse_flags(val):
        flags = {
            "reno_bathroom": 0,
            "reno_bedroom": 0,
            "reno_kitchen": 0,
            "reno_living_room": 0,
            "reno_other_custom": 0,
            "reno_full_renovation": 0
        }

        if pd.isna(val) or val == "":
            return flags

        if isinstance(val, str):
            try:
                parsed = eval(val)
            except:
                parsed = []
        else:
            parsed = val

        if not isinstance(parsed, list):
            return flags

        for room in parsed:
            r = str(room).lower()
            if "bathroom" in r:
                flags["reno_bathroom"] = 1
            elif "bedroom" in r:
                flags["reno_bedroom"] = 1
            elif "kitchen" in r:
                flags["reno_kitchen"] = 1
            elif "living" in r:
                flags["reno_living_room"] = 1
            elif "other" in r:
                flags["reno_other_custom"] = 1

        return flags

    flag_df = df["type_of_renovation"].apply(parse_flags).apply(pd.Series)
    df = pd.concat([df, flag_df], axis=1)

    # --------------------------------------------------
    # 5. Ensure numeric types
    # --------------------------------------------------
    numeric_cols = [
        "property_size",
        "renovation_cost",
        "sqft_renovated",
        "sqft_to_add",
        "structural_change"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --------------------------------------------------
    # 6. Select exact feature order
    # --------------------------------------------------
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

    return df[features]

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
target = "post_renovation_value"

# Drop missing targets
test_exp = test_exp.dropna(subset=[target])

# # Predict (row level)
X_test = test_exp[feature_columns]
y_test = test_exp[target].values

y_pred = model.predict(X_test)

# # Aggregate to property level
test_df = pd.DataFrame({
    "source_row": test_exp["source_row"].values,
    "y_true": y_test,
    "y_pred": y_pred
})

prop_level = test_df.groupby("source_row", as_index=False).agg(
    y_true=("y_true", "first"),
    y_pred=("y_pred", "mean")
)

# Metrics (property level)
prop_r2 = r2_score(prop_level["y_true"], prop_level["y_pred"])
prop_mape = mape(prop_level["y_true"], prop_level["y_pred"])

print("Property-level TEST R2:", prop_r2)
print("Property-level TEST MAPE:", prop_mape)

# # -----------------------
# # Preds real data
# # -----------------------
# real_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")

# # Ground truth (post renovation value)
# y_true = real_df["price"].astype(float)

# # Preprocess features
# real_df_processed = preprocess_real_data(real_df)

# # Ensure feature alignment
# real_X = real_df_processed[features]

# real_preds = model.predict(real_X)

# r2 = r2_score(y_true, real_preds)
# real_mape = mape(y_true, real_preds)

# print("Real Data R2:", r2)
# print("Real Data MAPE:", real_mape)


# -------------------------
# SAVE PREDICTIONS FOR WILCOXON
# -------------------------
svr_preds_path = "modelB/SVR/svr_train_synthetic_preds.csv"

# pred_df = pd.DataFrame({
#     "source_row": real_df.index,
#     "y_true": y_true.values,
#     "y_pred": real_preds
# })

pred_df = pd.DataFrame({
    "source_row": prop_level["y_true"].index,
    "y_true": prop_level["y_true"].values,
    "y_pred": prop_level["y_pred"].values
})

pred_df.to_csv(svr_preds_path, index=False)

