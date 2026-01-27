import pandas as pd
import json

df = pd.read_csv("synthetic_renovation_scenarios.csv")

def parse_types(value):
    try:
        return json.loads(value)
    except:
        return []

violations = []

for idx, row in df.iterrows():
    types = parse_types(row["renovation_type"])
    beds = row["bedrooms_to_reno"]
    baths = row["bathrooms_to_reno"]

    # rule 1: full renovation must have counts
    if types == ["Full renovation"]:
        if pd.isna(beds) or pd.isna(baths):
            violations.append((idx, "Full renovation missing bedroom/bathroom count"))

    # rule 2: Other/Custom only → counts must be 0
    if types == ["Other/Custom"]:
        if beds != 0 or baths != 0:
            violations.append((idx, "Other/Custom should have 0 bedrooms and bathrooms"))

    # rule 3a: Bedroom selected → bedrooms_to_reno > 0
    if "Bedroom" in types:
        if pd.isna(beds) or beds <= 0:
            violations.append((idx, "Bedroom selected but bedrooms_to_reno not set"))

    # rule 3b: Bathroom selected → bathrooms_to_reno > 0
    if "Bathroom" in types:
        if pd.isna(baths) or baths <= 0:
            violations.append((idx, "Bathroom selected but bathrooms_to_reno not set"))

# summary
print("Validation results")
print("------------------")
print("Total rows:", len(df))
print("Violations found:", len(violations))

if violations:
    print()
    print("First 10 violations:")
    for v in violations[:10]:
        print("Row", v[0], "→", v[1])
else:
    print("All rows passed validation")
