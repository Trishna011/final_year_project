import pandas as pd
from pathlib import Path
import random
from datasets import Dataset, DatasetDict

# ------------------------------------------------------
# Adds estimated pre-renovation cost of property to data
# ------------------------------------------------------

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

csv_path = PROJECT_ROOT.parent / "synthetic_renovation_scenarios_with_costs.csv"

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv(csv_path)

# Normalise column names to lower-case and trim whitespace so mappings are stable.
df.columns = df.columns.str.strip().str.lower()

print("Available columns:")
print(df.columns.tolist())

# -----------------------------
# Explicit column mapping
# -----------------------------
LOCATION_COL = "location"
SIZE_COL = "property_size"
RENOVATION_COST_COL = "renovation_cost"

# -----------------------------
# Price model
# -----------------------------

# BASE_PRICE_PER_SQFT: baseline market price per sqft used before adjustments.
BASE_PRICE_PER_SQFT = 284

# LOCATION_MULTIPLIER: multiplies base price for locality-based market differences.
LOCATION_MULTIPLIER = {
    "manchester city centre": 1.39,
    "salford": 1.41,
    "stockport": 0.98,
    "bolton": 0.85,
    "bury": 0.87,
    "oldham": 0.82,
    "rochdale": 0.64,
    "tameside": 0.81,
    "wigan": 0.57,
    "altrincham": 1.52,
    "prestwich": 1.04,
    "didsbury": 1.17,
    "chorlton": 1.36,
    "withington": 1.09,
    "levenshulme": 1.11,
    "sale": 1.33,
    "stretford": 1.12,
    "cheadle": 1.25,
    "ashton-under-lyne": 0.84,
    "trafford": 1.27,
}


# -----------------------------
# Condition inference (internal only)
# -----------------------------

def infer_condition(renovation_cost: float) -> int:
    if renovation_cost > 70000:
        return 1
    elif renovation_cost > 45000:
        return 2
    elif renovation_cost > 25000:
        return 3
    elif renovation_cost > 12000:
        return 4
    else:
        return 5

# CONDITION_DISCOUNT: multiplier applied to location-adjusted value based on inferred condition.
CONDITION_DISCOUNT = {
    1: 0.82,
    2: 0.88,
    3: 0.95,
    4: 1.00,
    5: 1.03,
}


# -----------------------------
# Core computation
# -----------------------------
def compute_pre_renovation_value(row):
    location = row[LOCATION_COL].strip().lower()
    size = row[SIZE_COL]
    renovation_cost = row[RENOVATION_COST_COL]

    if location not in LOCATION_MULTIPLIER:
        raise ValueError(f"Unknown location: {location}")

    base_value = size * BASE_PRICE_PER_SQFT
    location_adjusted = base_value * LOCATION_MULTIPLIER[location]

    condition = infer_condition(renovation_cost)
    condition_adjusted = location_adjusted * CONDITION_DISCOUNT[condition]

    noise = random.uniform(0.95, 1.05)

    final_value = condition_adjusted * noise

    return round(final_value, 2)


# -----------------------------
# Apply model
# -----------------------------
df["pre_renovation_cost"] = df.apply(
    compute_pre_renovation_value, axis=1
)

# -----------------------------
# Diagnostic check
# -----------------------------
mask = df["pre_renovation_cost"] < df[RENOVATION_COST_COL]

count = mask.sum()
total = len(df)
percentage = (count / total) * 100

print(
    f"Pre-renovation value < renovation cost in "
    f"{count} out of {total} rows ({percentage:.1f}%)."
)

# -----------------------------
# Save output locally
# -----------------------------
output_csv = (
    PROJECT_ROOT.parent
    / "synthetic_renovation_scenarios_with_pre_cost.csv"
)

df.to_csv(output_csv, index=False)
print(f"Saved local copy to {output_csv}")

# -----------------------------
# Push to Hugging Face
# -----------------------------
dataset = Dataset.from_pandas(df, preserve_index=False)
dataset_dict = DatasetDict({"train": dataset})

HF_REPO_NAME = "Trish101/reno_details_dataset"

dataset_dict.push_to_hub(
    HF_REPO_NAME,
    private=True
)

print(f"Dataset pushed to Hugging Face: {HF_REPO_NAME}")