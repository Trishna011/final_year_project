import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true))

# -------------------------------------------------------
# Load combined training dataset
# -------------------------------------------------------
real_train_df = pd.read_csv("processed_data/real_train_val_preprocessed.csv")

# -------------------------------------------------------
# Load Sentence BERT model
# -------------------------------------------------------
sbert = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------------------------------------
# Convert text descriptions into embeddings
# -------------------------------------------------------
X_text_train = sbert.encode(
    real_train_df["description"].tolist(),
    show_progress_bar=True
)

# -------------------------------------------------------
# Add location feature
# -------------------------------------------------------
loc_train = real_train_df["location"].values.reshape(-1, 1)

X_train = np.hstack([X_text_train, loc_train])

# -------------------------------------------------------
# Log transform target
# -------------------------------------------------------
y_train = np.log1p(real_train_df["price"].values)

# -------------------------------------------------------
# Initialize CatBoost regressor
# Early stopping removed because no validation set
# -------------------------------------------------------
model = CatBoostRegressor(
    iterations=1000,
    depth=8,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    verbose=100
)

# -------------------------------------------------------
# Train on full training dataset
# -------------------------------------------------------
model.fit(X_train, y_train)

# -------------------------------------------------------
# Load test dataset
# -------------------------------------------------------
real_test_preprocessed = pd.read_csv("processed_data/real_test_preprocessed.csv")

# -------------------------------------------------------
# Generate SBERT embeddings for test descriptions
# -------------------------------------------------------
X_text_test = sbert.encode(
    real_test_preprocessed["description"].tolist(),
    show_progress_bar=True
)

# -------------------------------------------------------
# Add location feature
# -------------------------------------------------------
loc_test = real_test_preprocessed["location"].values.reshape(-1, 1)

X_test = np.hstack([X_text_test, loc_test])

# -------------------------------------------------------
# Prepare true target
# -------------------------------------------------------
y_test_price = real_test_preprocessed["price"].values
y_test_log = np.log1p(y_test_price)

# -------------------------------------------------------
# Predict
# -------------------------------------------------------
test_preds_log = model.predict(X_test)

# -------------------------------------------------------
# Convert predictions back to price scale
# -------------------------------------------------------
test_preds_price = np.expm1(test_preds_log)

# -------------------------------------------------------
# Evaluate
# -------------------------------------------------------
r2_test = r2_score(y_test_log, test_preds_log)
mape_test = mean_absolute_percentage_error(y_test_price, test_preds_price)

print("Test R^2 (log price):", r2_test)
print("Test MAPE:", mape_test)
print("Test MAPE (%):", mape_test * 100)

# -------------------------------------------------------
# Save predictions
# -------------------------------------------------------
preds_path = "modelB/catBoost/sbert_catboost_real_test_preds.csv"

test_pred_df = pd.DataFrame({
    "id": real_test_preprocessed.index,
    "y_true": y_test_price,
    "y_pred": test_preds_price
})

test_pred_df.to_csv(preds_path, index=False)

print("Saved test predictions to", preds_path)
