import pandas as pd
import numpy as np
from scipy.stats import wilcoxon


def absolute_percentage_error(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])

# This controls overall false positive risk when running multiple tests
def holm_correction(p_values, alpha=0.05):
    p_values = np.array(p_values)
    m = len(p_values)

    # Sort p-values from smallest to largest
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    adjusted_alpha = np.array([alpha / (m - i) for i in range(m)])
    significant = np.zeros(m, dtype=bool)

    for i in range(m):
        if sorted_p[i] <= adjusted_alpha[i]:
            significant[i] = True
        else:
            break

    result = np.zeros(m, dtype=bool)
    result[sorted_indices] = significant

    return result, adjusted_alpha, sorted_p


# =========================
# LOAD MODELS
# =========================

catboost_real = pd.read_csv("modelB/catBoost/catboost_finetuned_real_predictions.csv")
lightgbm_real = pd.read_csv("modelB/lightGBM/lightgbm_finetuned_real_predictions.csv")
ftTransformer_real = pd.read_csv("modelB/ftTransformer/fttransformer_finetuned_real_predictions.csv")
rf_real = pd.read_csv("modelB/randomForest/randomForest_finetuned_real_predictions.csv")
ridge_real = pd.read_csv("modelB/ridgeRegression/ridge_finetuned_real_predictions.csv")
svr_real = pd.read_csv("modelB/SVR/svr_finetuned_real_predictions.csv")

catboost_errors_real = absolute_percentage_error(
    catboost_real["y_true"],
    catboost_real["y_pred"]
)

lightgbm_errors_real = absolute_percentage_error(
    lightgbm_real["y_true"],
    lightgbm_real["y_pred"]
)

ftTransformer_errors_real = absolute_percentage_error(
    ftTransformer_real["y_true"],
    ftTransformer_real["y_pred"]
)

rf_errors_real = absolute_percentage_error(
    rf_real["y_true"],
    rf_real["y_pred"]
)

ridge_errors_real = absolute_percentage_error(
    ridge_real["y_true"],
    ridge_real["y_pred"]
)

svr_errors_real = absolute_percentage_error(
    svr_real["y_true"],
    svr_real["y_pred"]
)

# =========================
# WILCOXON TEST
# =========================

p_values = []

def wilcoxon_test(catboost_errors_real, model2_errors_real, model2_name):

    stat_real, p_real = wilcoxon(
        catboost_errors_real,
        model2_errors_real,
        alternative="two-sided"
    )

    print(f"Raw p-value {model2_name}:", p_real)
    p_values.append(p_real)


wilcoxon_test(catboost_errors_real, lightgbm_errors_real, "lightGBM")
wilcoxon_test(catboost_errors_real, ftTransformer_errors_real, "ftTransformer")
wilcoxon_test(catboost_errors_real, rf_errors_real, "rf")
wilcoxon_test(catboost_errors_real, ridge_errors_real, "Ridge")
wilcoxon_test(catboost_errors_real, svr_errors_real, "SVR")


# =========================
# HOLM CORRECTION
# =========================

significant, adjusted_alpha, sorted_p = holm_correction(p_values, alpha=0.05)

for i, p in enumerate(p_values):
    print(f"Original p-value: {p}")
    print(f"Significant after Holm correction: {significant[i]}")