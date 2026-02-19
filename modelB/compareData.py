import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

# Load datasets
real_df = pd.read_csv("processed_data/real_train_val_with_predicted_reno_cost.csv")
syn_df  = pd.read_csv("processed_data/synthetic_train_expanded.csv")

# Keep only common columns
common_cols = list(set(real_df.columns).intersection(set(syn_df.columns)))

real_df = real_df[common_cols].copy()
syn_df  = syn_df[common_cols].copy()

print("Number of shared columns:", len(common_cols))

numeric_cols = real_df.select_dtypes(include=[np.number]).columns

stats = []

for col in numeric_cols:
    if col not in syn_df.columns:
        continue

    r = real_df[col].dropna()
    s = syn_df[col].dropna()

    if len(r) == 0 or len(s) == 0:
        continue

    stats.append({
        "feature": col,
        "real_mean": r.mean(),
        "syn_mean": s.mean(),
        "real_std": r.std(),
        "syn_std": s.std(),
        "real_p50": np.percentile(r, 50),
        "syn_p50": np.percentile(s, 50),
        "real_p95": np.percentile(r, 95),
        "syn_p95": np.percentile(s, 95),
    })

stats_df = pd.DataFrame(stats)
print(stats_df.sort_values("real_mean"))

categorical_cols = real_df.select_dtypes(include=["object"]).columns

for col in categorical_cols:
    if col not in syn_df.columns:
        continue

    print("\nFeature:", col)
    print("Real distribution:")
    print(real_df[col].value_counts(normalize=True).head())

    print("Synthetic distribution:")
    print(syn_df[col].value_counts(normalize=True).head())

num_common = [c for c in numeric_cols if c in syn_df.columns]

real_corr = real_df[num_common].corr()
syn_corr  = syn_df[num_common].corr()

corr_diff = (real_corr - syn_corr).abs()

print("Average absolute correlation difference:")
print(corr_diff.mean().mean())

real_df["is_real"] = 1
syn_df["is_real"]  = 0

combined = pd.concat([real_df, syn_df], axis=0)

combined = combined.dropna()

X = combined.drop(columns=["is_real"])
y = combined["is_real"]

X = pd.get_dummies(X, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)

probs = clf.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, probs)

print("Domain classifier AUC:", auc)
