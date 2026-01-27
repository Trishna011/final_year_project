import pandas as pd
from pathlib import Path
import random

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

# Normalise column names
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
BASE_PRICE_PER_SQFT = 260

LOCATION_MULTIPLIER = {
    "manchester city centre": 1.20,
    "salford": 1.05,
    "stockport": 1.00,
    "bolton": 0.85,
    "bury": 0.90,
    "oldham": 0.78,
    "rochdale": 0.75,
    "tameside": 0.88,
    "wigan": 0.82,
    "altrincham": 1.30,
    "prestwich": 1.10,
    "didsbury": 1.25,
    "chorlton": 1.20,
    "withington": 1.05,
    "levenshulme": 1.00,
    "sale": 1.15,
    "stretford": 1.05,
    "cheadle": 1.22,
    "ashton-under-lyne": 0.80,
    "trafford": 1.28,
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
# Save output
# -----------------------------
output_path = (
    PROJECT_ROOT.parent
    / "synthetic_renovation_scenarios_with_pre_renovation_values.csv"
)

df.to_csv(output_path, index=False)

print("Pre-renovation values generated successfully.")
