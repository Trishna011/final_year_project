import pandas as pd
import numpy as np

def absolute_percentage_error(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])


# =========================
# LOAD PREDICTIONS
# =========================

sbert_preds = pd.read_csv(
    "modelB/catBoost/sbert_catboost_real_preds.csv"
)

feature_preds = pd.read_csv(
    "modelB/catBoost/catboost_real_preds.csv"
)

# ensure same ordering by id
sbert_preds = sbert_preds.sort_values("id").reset_index(drop=True)
feature_preds = feature_preds.sort_values("id").reset_index(drop=True)

assert len(sbert_preds) == len(feature_preds), "Prediction lengths do not match"


# =========================
# COMPUTE ERRORS
# =========================

sbert_errors = absolute_percentage_error(
    sbert_preds["y_true"],
    sbert_preds["y_pred"]
)

feature_errors = absolute_percentage_error(
    feature_preds["y_true"],
    feature_preds["y_pred"]
)


# =========================
# FRACTION-BEST ANALYSIS
# =========================

sbert_wins = np.sum(sbert_errors < feature_errors)
feature_wins = np.sum(feature_errors < sbert_errors)
ties = np.sum(sbert_errors == feature_errors)

total = len(sbert_errors)

print("FRACTION-BEST RESULTS (REAL DATA)")
print("--------------------------------")
print(f"Sentence-BERT model wins: {sbert_wins} ({sbert_wins / total:.3f})")
print(f"Catboost only model wins: {feature_wins} ({feature_wins / total:.3f})")
print(f"Ties: {ties} ({ties / total:.3f})")


# =========================
# OPTIONAL SUMMARY STATISTICS
# =========================

print("\nMEAN ABSOLUTE PERCENTAGE ERROR")
print("--------------------------------")
print("Sentence-BERT:", np.mean(sbert_errors))
print("Catboost only:", np.mean(feature_errors))
