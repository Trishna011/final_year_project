import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
from modelB.catboost.catBoostFineTuned import run_test_predictions

y_test, test_preds, real_test, loaded_model, X_test, r2_catboost = run_test_predictions()

# --- Load data ---
train_df = pd.read_csv("processed_data/real_train_val_with_predicted_reno_cost.csv")

test_df = pd.read_csv("processed_data/real_test_with_predicted_reno_cost.csv")


# -----------------------------
# Normalize material text into consistent format
# -----------------------------
def normalize_material(x):
    if pd.isna(x):
        return np.nan
    return (
        str(x)
        .lower()
        .strip()
        .replace("_", "-")
        .replace(" ", "-")
    )

# -----------------------------
# Normalize renovation tokens
# -----------------------------
def normalize_token(x):
    return " ".join(x.lower().strip().split())

# -----------------------------
# Parse renovation type column into list format
# Converts string or list string into list format
# -----------------------------
def parse_reno(value):
    if pd.isna(value):
        return []
    value = str(value)
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [normalize_token(v) for v in parsed if isinstance(v, str)]
        except Exception:
            return []
    return [normalize_token(value)]


# -----------------------------
# Preprocess real dataset to match synthetic schema
# -----------------------------
def preprocess_real(df, require_target=False):
    
    if "type_of_renovation" in df.columns:
        # Clean renovation type column
        df["type_of_renovation"] = df["type_of_renovation"].astype(str).str.strip().str.lower()
        df = df[~df["type_of_renovation"].isin(["", "nan", "none", "null"])]

        # Encode material grade ordinally
        material_mapping = {
            "budget-friendly": 0,
            "mid-range": 1,
            "high-end": 2
        }

        df["material_grade"] = df["material_grade"].apply(normalize_material)
        df["material_grade"] = df["material_grade"].map(material_mapping)
        df["material_grade"] = df["material_grade"].astype(float)

    
        # Parse renovation types into structured form
        df["type_of_renovation_parsed"] = df["type_of_renovation"].apply(parse_reno)

        # Create one hot features for renovation types
        fixed_types = {
            "bathroom": "bathroom",
            "bedroom": "bedroom",
            "kitchen": "kitchen",
            "living room": "living_room",
            "other/custom": "other_custom",
            "full renovation": "full_renovation"
        }

        for suffix in fixed_types.values():
            df[f"reno_{suffix}"] = 0

        for key, suffix in fixed_types.items():
            df[f"reno_{suffix}"] = df["type_of_renovation_parsed"].apply(lambda lst: int(key in lst))

        # Drop unused columns
        df = df.drop(
            columns=["type_of_renovation", "type_of_renovation_parsed", "id", "extended_rooms"],
            errors="ignore"
        )

        df["post_renovation_value"] = df["price"]

        # structural_change naming consistency - needed here as you didn't save synth feature cols
        if "structural_changes" in df.columns:
            df["structural_change"] = df["structural_changes"].astype(int)

    else:
        # Ensure correct types
        df["material_grade"] = df["material_grade"].astype(float)

        df = df.drop(
            columns=["source_row"],
            errors="ignore"
        )
    return df

train_df = preprocess_real(train_df)
test_df = preprocess_real(test_df)


# --- Step 2: Calculate price per sqft per location from TRAINING data only ---
train_df = train_df.copy()
train_df["price_per_sqft"] = train_df["price"] / train_df["property_size"]

location_price_per_sqft = train_df.groupby("Location")["price_per_sqft"].mean()
global_price_per_sqft = train_df["price_per_sqft"].mean()  # fallback for unseen locations

print("Price per sqft by location:")
print(location_price_per_sqft.sort_values(ascending=False).to_string())
print(f"\nGlobal fallback price per sqft: £{global_price_per_sqft:,.2f}")

# --- Step 3: Apply to test set ---
test_df = test_df.copy()
test_df["price_per_sqft"] = test_df["Location"].map(location_price_per_sqft)

# How many test locations were unseen in training?
unseen = test_df["price_per_sqft"].isna().sum()
print(f"\n{unseen} properties had unseen locations — using global fallback")
test_df["price_per_sqft"].fillna(global_price_per_sqft, inplace=True)

# Rule-based prediction: property_size × price_per_sqft for that location
rule_based_preds = test_df["property_size"] * test_df["price_per_sqft"]
y_test_real = test_df["price"]

# --- Step 4: Manual metrics ---
def mape(actual, predicted):
    return np.mean(np.abs((actual - predicted) / actual)) * 100

rmse  = np.sqrt(mean_squared_error(y_test_real, rule_based_preds))
mae   = mean_absolute_error(y_test_real, rule_based_preds)
r2    = r2_score(y_test_real, rule_based_preds)
mean_abs  = mape(y_test_real, rule_based_preds)

print("RMSE: ", rmse)
print("MAE: ", mae)
print("R2: ", r2)
print("MAPE: ", mean_abs)

# --- Save predictions ---
preds_df = pd.DataFrame({
    "y_true": y_test_real.values,
    "y_pred": rule_based_preds.values
})

preds_df.to_csv("modelB/manualModel/manual_train_real_preds.csv", index=False)




# --- Step 6: Side by side scatter plot ---
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, preds, title, r2 in zip(
    axes,
    [rule_based_preds.values, test_preds],
    ["Non-AI: Price per sq ft by Location", "AI Model: CatBoost"],
    [r2, r2_catboost]
):
    y_actual = y_test_real.values if title.startswith("Non") else y_test

    ax.scatter(y_actual, preds, color="#2878B5", alpha=0.7,
               edgecolors="white", linewidth=0.5)
    min_val = min(min(y_actual), min(preds))
    max_val = max(max(y_actual), max(preds))
    ax.plot([min_val, max_val], [min_val, max_val],
            color="red", linewidth=2, linestyle="--", label="Perfect Prediction")
    ax.annotate(f"R² = {r2:.3f}",
                xy=(0.05, 0.95), xycoords="axes fraction",
                fontsize=12, va="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"))
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Actual Post-Renovation Value (£)", fontsize=12)
    ax.set_ylabel("Predicted Post-Renovation Value (£)", fontsize=12)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle("AI Model vs Non-AI Baseline — Post-Renovation Property Valuation",
             fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()