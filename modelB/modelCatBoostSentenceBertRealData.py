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


sbert = SentenceTransformer("all-MiniLM-L6-v2")

X_text_train = sbert.encode(
    real_train_df["description"].tolist(),
    show_progress_bar=True
)

X_text_val = sbert.encode(
    real_val_preprocessed["description"].tolist(),
    show_progress_bar=True
)

loc_train = real_train_df["location"].values.reshape(-1, 1)
loc_val = real_val_preprocessed["location"].values.reshape(-1, 1)

X_train = np.hstack([X_text_train, loc_train])
X_val = np.hstack([X_text_val, loc_val])

y_train = np.log1p(real_train_df["price"].values)
y_val_true = real_val_preprocessed["price"].values

model = CatBoostRegressor(
    iterations=1000,
    depth=8,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    early_stopping_rounds=50,
    verbose=100
)

model.fit(
    X_train,
    y_train,
    eval_set=(X_val, np.log1p(y_val_true))
)


y_val_log = np.log1p(real_val_preprocessed["price"].values)

val_preds_log = model.predict(X_val)

# convert predictions back to original price scale
val_preds_price = np.expm1(val_preds_log)
y_val_price = real_val_preprocessed["price"].values

mape = mean_absolute_percentage_error(y_val_price, val_preds_price)


r2 = r2_score(y_val_log, val_preds_log)

print("R^2 (log price):", r2)
print("MAPE:", mape)
print("MAPE (%):", mape * 100)


