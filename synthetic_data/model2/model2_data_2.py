from pathlib import Path
import json
import sys
import pandas as pd

# -----------------------------------------
# Adds renovation cost to data from model 1
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

INPUT_CSV = PROJECT_ROOT.parent/"synthetic_renovation_scenarios.csv"
OUTPUT_CSV = PROJECT_ROOT.parent/"synthetic_renovation_scenarios_with_costs.csv"

sys.path.append(str(PROJECT_ROOT.parent))
from model.featureEngineering import expand_records, add_labour_rate, prediction

# -------------------------
# Load CSV correctly
# -------------------------

df = pd.read_csv(INPUT_CSV)

# These columns were saved as JSON-encoded strings; convert them back to Python objects.
JSON_COLS = [
    "renovation_type",
    "sqft_renovated",
    "sqft_to_add",
    "material_grade",
    "structural_changes"
]

for col in JSON_COLS:
    # json.loads will convert the string representation back to lists/dicts
    df[col] = df[col].apply(json.loads)

#Convert DataFrame rows to plain dict records for processing by the feature-engineering functions.
records = df.to_dict(orient="records")

# -------------------------
# Run Model 1
# -------------------------

costs = []

for idx, record in enumerate(records):

    # expand_records: convert a high-level renovation job into itemized rows
    # e.g. separate bedrooms, bathrooms, kitchens, and extensions into individual entries.
    expanded = expand_records(record)

    # add_labour_rate
    total_cost = 0.0
    for r in expanded:
        r = add_labour_rate(r)

        # prediction: returns the estimated cost for the single expanded item.
        total_cost += float(prediction(r))

    costs.append(total_cost)

    #print progress as there is alot of data
    if idx % 500 == 0:
        print(f"Processed {idx}/{len(records)} rows")

# -------------------------
# Save CSV
# -------------------------

# Add the computed renovation cost column to the original DataFrame.
df["renovation_cost"] = costs

# Re-serialize the JSON columns back to strings so the CSV stores them as before.
for col in JSON_COLS:
    df[col] = df[col].apply(json.dumps)

df.to_csv(OUTPUT_CSV, index=False)

print(f"Saved {len(df)} rows to {OUTPUT_CSV}")
