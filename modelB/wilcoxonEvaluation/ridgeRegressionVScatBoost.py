import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

def absolute_percentage_error(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])


# =========================
# REAL DATA COMPARISON
# =========================

ridge_real = pd.read_csv(
    "modelB/ridgeRegression/ridge_real_preds.csv"
)

catboost_real = pd.read_csv(
    "modelB/catBoost/catboost_real_preds.csv"
)

ridge_errors_real = absolute_percentage_error(
    ridge_real["y_true"],
    ridge_real["y_pred"]
)

catboost_errors_real = absolute_percentage_error(
    catboost_real["y_true"],
    catboost_real["y_pred"]
)

stat_real, p_real = wilcoxon(
    ridge_errors_real,
    catboost_errors_real,
    alternative="two-sided"
)

print("REAL DATA")
print("Wilcoxon statistic:", stat_real)
print("p-value:", p_real)

#explain why p of 0.05 was chosen
if p_real < 0.05:
    print("Statistically significant difference\n")
else:
    print("No statistically significant difference\n")


# =========================
# SYNTHETIC DATA COMPARISON
# =========================

ridge_syn = pd.read_csv(
    "modelB/ridgeRegression/ridge_synthetic_preds.csv"
)

catboost_syn = pd.read_csv(
    "modelB/catBoost/catboost_synthetic_preds.csv"
)

ridge_errors_syn = absolute_percentage_error(
    ridge_syn["y_true"],
    ridge_syn["y_pred"]
)

catboost_errors_syn = absolute_percentage_error(
    catboost_syn["y_true"],
    catboost_syn["y_pred"]
)

stat_syn, p_syn = wilcoxon(
    ridge_errors_syn,
    catboost_errors_syn,
    alternative="two-sided"
)

print("SYNTHETIC DATA")
print("Wilcoxon statistic:", stat_syn)
print("p-value:", p_syn)

if p_syn < 0.05:
    print("Statistically significant difference")
else:
    print("No statistically significant difference")
