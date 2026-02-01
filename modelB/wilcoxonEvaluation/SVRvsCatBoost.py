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

catboost_real = pd.read_csv(
    "modelB/catBoost/catboost_real_preds.csv"
)

svr_real = pd.read_csv(
    "modelB/svr/svr_real_preds.csv"
)

catboost_errors_real = absolute_percentage_error(
    catboost_real["y_true"],
    catboost_real["y_pred"]
)

svr_errors_real = absolute_percentage_error(
    svr_real["y_true"],
    svr_real["y_pred"]
)

stat_real, p_real = wilcoxon(
    catboost_errors_real,
    svr_errors_real,
    alternative="two-sided"
)

print("REAL DATA")
print("Wilcoxon statistic:", stat_real)
print("p-value:", p_real)

if p_real < 0.05:
    print("Statistically significant difference\n")
else:
    print("No statistically significant difference\n")


# =========================
# SYNTHETIC DATA COMPARISON
# =========================

catboost_syn = pd.read_csv(
    "modelB/catBoost/catboost_synthetic_preds.csv"
)

svr_syn = pd.read_csv(
    "modelB/svr/svr_synthetic_preds.csv"
)

catboost_errors_syn = absolute_percentage_error(
    catboost_syn["y_true"],
    catboost_syn["y_pred"]
)

svr_errors_syn = absolute_percentage_error(
    svr_syn["y_true"],
    svr_syn["y_pred"]
)

stat_syn, p_syn = wilcoxon(
    catboost_errors_syn,
    svr_errors_syn,
    alternative="two-sided"
)

print("SYNTHETIC DATA")
print("Wilcoxon statistic:", stat_syn)
print("p-value:", p_syn)

if p_syn < 0.05:
    print("Statistically significant difference")
else:
    print("No statistically significant difference")
