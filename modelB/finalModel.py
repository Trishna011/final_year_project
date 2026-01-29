import json
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from catboost import CatBoostRegressor

# load real model
real_model = CatBoostRegressor()
real_model.load_model("modelB/models/real_catboost_model.cbm")

# load schema used by real model
with open("modelB/models/real_feature_columns.json", "r") as f:
    REAL_FEATURE_COLS = json.load(f)

df_syn = pd.read_csv("processed_data/synthetic_val_expanded.csv")

# rename columns so they match
df_syn = df_syn.rename(columns={
    "structural_change": "structural_changes"
})

# pad missing features
for col in REAL_FEATURE_COLS:
    if col not in df_syn.columns:
        df_syn[col] = 0

# build X
X_real = df_syn[REAL_FEATURE_COLS].values

# predict
df_syn["pred_price_real_model"] = np.expm1(real_model.predict(X_real))


# load synthetic model
syn_model = CatBoostRegressor()
syn_model.load_model("modelB/models/synthetic_catboost_model.cbm")

with open("modelB/models/synthetic_feature_columns.json", "r") as f:
    SYN_FEATURE_COLS = json.load(f)

# pad missing features
for col in SYN_FEATURE_COLS:
    if col not in df_syn.columns:
        df_syn[col] = 0

X_syn = df_syn[SYN_FEATURE_COLS].values

# real model (log trained)
df_syn["pred_price_real_model"] = np.expm1(
    real_model.predict(X_real)
)

# synthetic model (raw trained)
df_syn["pred_price_synthetic_model"] = syn_model.predict(X_syn)

y_true = df_syn["post_renovation_value"].values
pred_syn = df_syn["pred_price_synthetic_model"].values
pred_real = df_syn["pred_price_real_model"].values

results = []

#find which is the best low and the best high to use
# for low in [0.6, 0.7, 0.8, 0.9]:
#     for high in [1.1, 1.2, 1.3, 1.4, 1.5]:
#         if low >= high:
#             continue

#         pred_hybrid = np.clip(
#             pred_syn,
#             low * pred_real,
#             high * pred_real
#         )

#         r2 = r2_score(y_true, pred_hybrid)

#         mae = np.mean(np.abs(y_true - pred_hybrid))

#         ratio = pred_hybrid / np.clip(pred_real, 1e-6, None)
#         extreme = np.mean((ratio < low) | (ratio > high))

#         results.append({
#             "low": low,
#             "high": high,
#             "r2": r2,
#             "mae": mae,
#             "extreme_rate": extreme
#         })

# results_df = pd.DataFrame(results)
# print(results_df.sort_values("r2", ascending=False).head(10))


# #combine hybrid and synthetic model
# • The synthetic model decides the price most of the time.
# • The real model only intervenes when the synthetic price looks unrealistic.
# • The real model never fully replaces the synthetic model.
lower = 0.6 * df_syn["pred_price_real_model"]
upper = 1.5 * df_syn["pred_price_real_model"]

df_syn["pred_price_hybrid"] = np.clip(
    df_syn["pred_price_synthetic_model"],
    lower,
    upper
)

r2_syn = r2_score(
    df_syn["post_renovation_value"],
    df_syn["pred_price_hybrid"]
)
print("Hybrid R2 vs synthetic target:", r2_syn)

mae = np.mean(
    np.abs(df_syn["post_renovation_value"] - df_syn["pred_price_hybrid"])
)

mape = np.mean(
    np.abs(
        (df_syn["post_renovation_value"] - df_syn["pred_price_hybrid"]) /
        df_syn["post_renovation_value"]
    )
) * 100

print("Hybrid MAPE:", mape)
