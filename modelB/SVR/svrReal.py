import numpy as np
import pandas as pd
import ast
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVR
from sklearn.metrics import r2_score
from sklearn.impute import SimpleImputer


def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))


# =========================
# LOAD DATA
# =========================

train_df = pd.read_csv("processed_data/real_with_extracted_features_synonyms.csv")
val_df = pd.read_csv("processed_data/real_val_with_extracted_features_synonyms.csv")

train_df = train_df.drop_duplicates().reset_index(drop=True)
val_df = val_df.drop_duplicates().reset_index(drop=True)

# =========================
# REMOVE OUTLIERS (TRAIN ONLY)
# =========================

Q1 = train_df["price"].quantile(0.25)
Q3 = train_df["price"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

train_df = train_df[
    (train_df["price"] >= lower) &
    (train_df["price"] <= upper)
].reset_index(drop=True)

# =========================
# MATERIAL GRADE ENCODING
# =========================

material_mapping = {
    "budget-friendly": 0,
    "mid-range": 1,
    "high-end": 2
}

for df in [train_df, val_df]:
    df["material_grade"] = df.get("material_grade", np.nan).map(material_mapping)

# =========================
# STRUCTURAL CHANGES
# =========================

le_structural = LabelEncoder()
train_df["structural_changes"] = le_structural.fit_transform(
    train_df["structural_changes"].astype(str)
)
val_df["structural_changes"] = le_structural.transform(
    val_df["structural_changes"].astype(str)
)

# =========================
# RENOVATION TYPE ONE HOT
# =========================

def normalize_token(x):
    return " ".join(x.lower().strip().split())

def parse_reno(value):
    if pd.isna(value):
        return []
    value = str(value)
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [normalize_token(v) for v in parsed]
        except Exception:
            return []
    return [normalize_token(value)]

train_df["reno_parsed"] = train_df["type_of_renovation"].apply(parse_reno)
val_df["reno_parsed"] = val_df["type_of_renovation"].apply(parse_reno)

fixed_types = {
    "bathroom": "bathroom",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
    "living room": "living_room",
    "other/custom": "other_custom",
    "full renovation": "full_renovation"
}

for key, suffix in fixed_types.items():
    train_df[f"reno_{suffix}"] = train_df["reno_parsed"].apply(lambda x: int(key in x))
    val_df[f"reno_{suffix}"] = val_df["reno_parsed"].apply(lambda x: int(key in x))

train_df = train_df.drop(columns=["type_of_renovation", "reno_parsed"])
val_df = val_df.drop(columns=["type_of_renovation", "reno_parsed"])

# =========================
# FEATURE SELECTION
# =========================

DROP_FEATURES = [
    "id",
    "description",
    "num_of_bedrooms",
    "num_of_bathrooms",
    "price"
]

feature_cols = [c for c in train_df.columns if c not in DROP_FEATURES]

# clip property size
lower = train_df["property_size"].quantile(0.01)
upper = train_df["property_size"].quantile(0.99)

for df in [train_df, val_df]:
    df["property_size"] = df["property_size"].clip(lower, upper)

# =========================
# MATRICES
# =========================

X_train = train_df[feature_cols]
X_val = val_df[feature_cols]

y_train_log = np.log1p(train_df["price"].values)
y_val_log = np.log1p(val_df["price"].values)

# one hot encode categoricals
X_train = pd.get_dummies(X_train, drop_first=True)
X_val = pd.get_dummies(X_val, drop_first=True)

X_val = X_val.reindex(columns=X_train.columns, fill_value=0)

# =========================
# IMPUTE + SCALE
# =========================

imputer = SimpleImputer(strategy="median")
scaler = StandardScaler()

X_train_imp = imputer.fit_transform(X_train)
X_val_imp = imputer.transform(X_val)

X_train_scaled = scaler.fit_transform(X_train_imp)
X_val_scaled = scaler.transform(X_val_imp)

# =========================
# TRAIN SVR
# =========================

svr_model = SVR(
    kernel="rbf",
    C=100,
    epsilon=0.1,
    gamma="scale"
)

svr_model.fit(X_train_scaled, y_train_log)

# =========================
# PREDICT
# =========================

val_preds_log = svr_model.predict(X_val_scaled)

val_preds_price = np.expm1(val_preds_log)
y_val_price = val_df["price"].values

# =========================
# SAVE PREDICTIONS FOR WILCOXON
# =========================

svr_preds_path = "modelB/svr/svr_real_preds.csv"

pred_df = pd.DataFrame({
    "id": val_df.index,
    "y_true": y_val_price,
    "y_pred": val_preds_price
})

pred_df.to_csv(svr_preds_path, index=False)
print(f"Saved SVR real predictions to {svr_preds_path}")

# =========================
# METRICS
# =========================

r2 = r2_score(y_val_log, val_preds_log)
mape = mean_absolute_percentage_error(y_val_price, val_preds_price)

print("SVR R^2 (log price):", r2)
print("SVR MAPE:", mape)
print("SVR MAPE (%):", mape * 100)
