import random
import json
import pandas as pd

NUM_SAMPLES = 10
OUTPUT_FILE = "synthetic_renovation_scenarios.csv"

MATERIAL_GRADES = ["High-end", "Mid-range", "Budget-friendly"]

LOCATIONS = [
    "Manchester City Centre", "Salford", "Stockport", "Bolton", "Bury",
    "Oldham", "Rochdale", "Tameside", "Trafford", "Wigan", "Altrincham",
    "Ashton-under-Lyne", "Prestwich", "Didsbury", "Chorlton",
    "Withington", "Levenshulme", "Sale", "Stretford", "Cheadle"
]

LOCATION_SIZE_RULES = {
    "Manchester City Centre": (400, 750),
    "Salford": (400, 900),
    "Didsbury": (700, 1400),
    "Chorlton": (700, 1400),
    "Withington": (650, 1300),
    "Levenshulme": (650, 1200),
    "Prestwich": (700, 1400),
    "Ashton-under-Lyne": (650, 1600),
    "Tameside": (650, 1600),
    "Bolton": (700, 1800),
    "Bury": (700, 1700),
    "Oldham": (650, 1600),
    "Rochdale": (650, 1700),
    "Stockport": (700, 1800),
    "Sale": (800, 2000),
    "Stretford": (750, 1800),
    "Altrincham": (900, 2500),
    "Cheadle": (900, 2500),
    "Trafford": (800, 2200),
    "Wigan": (700, 1800)
}

def yes_no(p):
    return "Yes" if random.random() < p else "No"

RENOVATION_SCENARIOS = [
    ["Full renovation"],

    ["Bedroom"], ["Bathroom"], ["Kitchen"], ["Living room"], ["Other/Custom"],

    ["Bedroom", "Bathroom"],
    ["Bedroom", "Kitchen"],
    ["Bedroom", "Living room"],
    ["Bedroom", "Other/Custom"],

    ["Bathroom", "Kitchen"],
    ["Bathroom", "Living room"],
    ["Bathroom", "Other/Custom"],

    ["Living room", "Kitchen"],
    ["Kitchen", "Other/Custom"],
    ["Living room", "Other/Custom"],

    ["Living room", "Kitchen", "Other/Custom"],
    ["Bedroom", "Bathroom", "Kitchen"],
    ["Bedroom", "Bathroom", "Living room"],
    ["Bedroom", "Bathroom", "Other/Custom"]
]

rows = []

while len(rows) < NUM_SAMPLES:

    location = random.choice(LOCATIONS)
    min_sqft, max_sqft = LOCATION_SIZE_RULES[location]
    property_size = random.randint(min_sqft, max_sqft)

    renovation_type = random.choice(RENOVATION_SCENARIOS)
    is_full = renovation_type == ["Full renovation"]

    max_extension_total = int(property_size * 0.35)

    if is_full:
        bedrooms = random.randint(1, 5)
        bathrooms = random.randint(1, 3)

        renovated_sqft = random.randint(
            int(property_size * 0.6),
            int(property_size * 0.9)
        )

        extension_sqft = random.randint(
            0,
            int(property_size * 0.3)
        )

        sqft_renovated = {
            "bedrooms": [],
            "bathrooms": [],
            "other": {"Full renovation": renovated_sqft}
        }

        sqft_to_add = {
            "bedrooms": [0] * bedrooms,
            "bathrooms": [0] * bathrooms,
            "other": {"Full renovation": extension_sqft}
        }

        material_grade = {
            "bedrooms": [],
            "bathrooms": [],
            "other": {
                "Full renovation": random.choice(MATERIAL_GRADES)
            }
        }

        structural_changes = [yes_no(0.8)]

    else:
        bedrooms = random.randint(1, 4) if "Bedroom" in renovation_type else 0
        bathrooms = random.randint(1, 3) if "Bathroom" in renovation_type else 0

        sqft_renovated = {
            "bedrooms": [random.randint(80, 220) for _ in range(bedrooms)],
            "bathrooms": [random.randint(35, 120) for _ in range(bathrooms)],
            "other": {}
        }

        sqft_to_add = {
            "bedrooms": [random.randint(0, 250) for _ in range(bedrooms)],
            "bathrooms": [random.randint(0, 120) for _ in range(bathrooms)],
            "other": {}
        }

        for room in renovation_type:
            if room == "Kitchen":
                sqft_renovated["other"][room] = random.randint(120, 350)
                sqft_to_add["other"][room] = random.randint(0, 350)
            elif room == "Living room":
                sqft_renovated["other"][room] = random.randint(150, 450)
                sqft_to_add["other"][room] = random.randint(0, 450)
            elif room == "Other/Custom":
                sqft_renovated["other"][room] = random.randint(80, 300)
                sqft_to_add["other"][room] = random.randint(0, 300)

        material_grade = {
            "bedrooms": [random.choice(MATERIAL_GRADES) for _ in range(bedrooms)],
            "bathrooms": [random.choice(MATERIAL_GRADES) for _ in range(bathrooms)],
            "other": {
                r: random.choice(MATERIAL_GRADES)
                for r in sqft_renovated["other"]
            }
        }

        total_items = bedrooms + bathrooms + len(sqft_renovated["other"])
        structural_changes = [yes_no(0.7) for _ in range(total_items)]

    total_sqft_added = (
        sum(sqft_to_add["bedrooms"]) +
        sum(sqft_to_add["bathrooms"]) +
        sum(sqft_to_add["other"].values())
    )

    if total_sqft_added > max_extension_total:
        continue

    rows.append({
        "renovation_type": json.dumps(renovation_type),
        "bedrooms_to_reno": bedrooms,
        "bathrooms_to_reno": bathrooms,
        "sqft_renovated": json.dumps(sqft_renovated),
        "sqft_to_add": json.dumps(sqft_to_add),
        "material_grade": json.dumps(material_grade),
        "structural_changes": json.dumps(structural_changes),
        "property_size": property_size,
        "Location": location
    })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_FILE, index=False)

print(f"Generated {len(df)} records")
