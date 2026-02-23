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
    "modelB/catBoost/catboost_finetuned_real_predictions.csv"
)

rf_real = pd.read_csv(
    "modelB/catBoost/catboost_train_real_preds.csv"
)

catboost_errors_real = absolute_percentage_error(
    catboost_real["y_true"],
    catboost_real["y_pred"]
)

catboost_errors_synth = absolute_percentage_error(
    rf_real["y_true"],
    rf_real["y_pred"]
)

stat_real, p_real = wilcoxon(
    catboost_errors_real,
    catboost_errors_synth,
    alternative="two-sided"
)

print("REAL DATA")
print("Wilcoxon statistic:", stat_real)
print("p-value:", p_real)

if p_real < 0.05:
    print("Statistically significant difference\n")
else:
    print("No statistically significant difference\n")

