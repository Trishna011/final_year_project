import json
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from catboost import CatBoostRegressor

# load real model
real_model = CatBoostRegressor()
real_model.load_model("modelB/models/real_catboost_model.cbm")

# load synthetic model
syn_model = CatBoostRegressor()
syn_model.load_model("modelB/models/synthetic_catboost_model.cbm")

# load schema used by real model
with open("modelB/models/real_feature_columns.json", "r") as f:
    REAL_FEATURE_COLS = json.load(f)

with open("modelB/models/synthetic_feature_columns.json", "r") as f:
    SYN_FEATURE_COLS = json.load(f)

df_syn = pd.read_csv("processed_data/synthetic_val_expanded.csv")

def value_prediction(df):
    df = df.copy()

    # rename columns
    if "structural_change" in df.columns:
        df = df.rename(columns={
            "structural_change": "structural_changes"
        })

    # pad real model features
    for col in REAL_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0

    X_real = df[REAL_FEATURE_COLS]
    pred_real = np.expm1(real_model.predict(X_real))

    # pad synthetic model features
    for col in SYN_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0

    X_syn = df[SYN_FEATURE_COLS]
    pred_syn = syn_model.predict(X_syn)

    #results = []

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
    # mimicing human in the loop systems 
    # hybrid logic
    lower = 0.6 * pred_real
    upper = 1.5 * pred_real

    pred_hybrid = np.clip(
        pred_syn,
        lower,
        upper
    )

    return pred_hybrid

df_syn["pred_price_hybrid"] = value_prediction(df_syn)

r2 = r2_score(
    df_syn["post_renovation_value"],
    df_syn["pred_price_hybrid"]
)
print("Hybrid R2 vs synthetic target:", r2)

mape = np.mean(
    np.abs(
        (df_syn["post_renovation_value"] - df_syn["pred_price_hybrid"]) /
        df_syn["post_renovation_value"]
    )
) * 100
print("Hybrid MAPE:", mape)
