import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))

real_train_df = pd.read_csv("processed_data/real_train_preprocessed.csv")
real_val_preprocessed = pd.read_csv("processed_data/real_val_preprocessed.csv")

# -------------------------------------------------------
# Load Sentence BERT model
# This converts property descriptions into dense vectors
# -------------------------------------------------------
sbert = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------------------------------------
# Convert text descriptions into embeddings
# Each description becomes a numeric vector
# -------------------------------------------------------
X_text_train = sbert.encode(
    real_train_df["description"].tolist(),
    show_progress_bar=True
)

X_text_val = sbert.encode(
    real_val_preprocessed["description"].tolist(),
    show_progress_bar=True
)

# -------------------------------------------------------
# Add location as an additional numeric feature
# Location was already encoded earlier in preprocessing
# -------------------------------------------------------
loc_train = real_train_df["location"].values.reshape(-1, 1)
loc_val = real_val_preprocessed["location"].values.reshape(-1, 1)

# Combine text embeddings and location into final feature matrix
X_train = np.hstack([X_text_train, loc_train])
X_val = np.hstack([X_text_val, loc_val])

# -------------------------------------------------------
# Log transform price
# This reduces skew and stabilizes variance
# The model learns log(price), not raw price
# -------------------------------------------------------
y_train = np.log1p(real_train_df["price"].values)
y_val_true = real_val_preprocessed["price"].values

# -------------------------------------------------------
# Initialize CatBoost regressor
# RMSE is applied in log space
# Early stopping prevents overfitting
# -------------------------------------------------------
model = CatBoostRegressor(
    iterations=1000,
    depth=8,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    early_stopping_rounds=50,
    verbose=100
)

# -------------------------------------------------------
# Train model using validation set for early stopping
# Validation target is also log transformed
# -------------------------------------------------------
model.fit(
    X_train,
    y_train,
    eval_set=(X_val, np.log1p(y_val_true))
)

# -------------------------------------------------------
# Make predictions on validation set
# Predictions are in log scale
# -------------------------------------------------------
y_val_log = np.log1p(real_val_preprocessed["price"].values)
val_preds_log = model.predict(X_val)
# -------------------------------------------------------
# Convert predictions back to original price scale
# expm1 reverses log1p transformation
# -------------------------------------------------------
val_preds_price = np.expm1(val_preds_log)
y_val_price = real_val_preprocessed["price"].values

# =========================
# SAVE PREDICTIONS FOR EVALUATION
# =========================

preds_path = "modelB/catBoost/sbert_catboost_real_preds.csv"

pred_df = pd.DataFrame({
    "id": real_val_preprocessed.index,
    "y_true": y_val_price,
    "y_pred": val_preds_price
})

pred_df.to_csv(preds_path, index=False)

print(f"Saved Sentence-BERT CatBoost predictions to {preds_path}")


mape = mean_absolute_percentage_error(y_val_price, val_preds_price)


r2 = r2_score(y_val_log, val_preds_log)

print("R^2 (log price):", r2)
print("MAPE:", mape)
print("MAPE (%):", mape * 100)


