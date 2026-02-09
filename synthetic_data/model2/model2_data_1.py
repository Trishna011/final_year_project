#this file simulates user's using the website and inputting different combinations of renovation features 

import random
import json
import pandas as pd

NUM_SAMPLES = 8000
OUTPUT_FILE = "synthetic_renovation_scenarios.csv"

MATERIAL_GRADES = ["High-end", "Mid-range", "Budget-friendly"]

LOCATIONS = [
    "Manchester City Centre", "Salford", "Stockport", "Bolton", "Bury",
    "Oldham", "Rochdale", "Tameside", "Trafford", "Wigan", "Altrincham",
    "Ashton-under-Lyne", "Prestwich", "Didsbury", "Chorlton",
    "Withington", "Levenshulme", "Sale", "Stretford", "Cheadle"
]

# LOCATION_SIZE_RULES = {
#     "Manchester City Centre": (400, 750),
#     "Salford": (400, 900),
#     "Didsbury": (700, 1400),
#     "Chorlton": (700, 1400),
#     "Withington": (650, 1300),
#     "Levenshulme": (650, 1200),
#     "Prestwich": (700, 1400),
#     "Ashton-under-Lyne": (650, 1600),
#     "Tameside": (650, 1600),
#     "Bolton": (700, 1800),
#     "Bury": (700, 1700),
#     "Oldham": (650, 1600),
#     "Rochdale": (650, 1700),
#     "Stockport": (700, 1800),
#     "Sale": (800, 2000),
#     "Stretford": (750, 1800),
#     "Altrincham": (900, 2500),
#     "Cheadle": (900, 2500),
#     "Trafford": (800, 2200),
#     "Wigan": (700, 1800)
# }

# Mapping of location -> (min_sqft, max_sqft).
# These ranges model different typical property sizes by area and are used to
# randomly sample a property's total floor area for each synthetic record.
LOCATION_SIZE_RULES = {
    "Manchester City Centre": (300, 2300),
    "Salford": (400, 2500),
    "Didsbury": (900, 2200),
    "Chorlton": (1100, 1800),
    "Withington": (900, 3300),
    "Levenshulme": (700, 2200),
    "Prestwich": (1300, 5200),
    "Ashton-under-Lyne": (1600, 2300),
    "Tameside": (2500, 4500),
    "Bolton": (3000, 3800),
    "Bury": (500, 3600),
    "Oldham": (2500, 3300),
    "Rochdale": (900, 3000),
    "Stockport": (700, 1200),
    "Sale": (800, 1200),
    "Stretford": (1800, 2200),
    "Altrincham": (6000, 7500),
    "Cheadle": (1400, 3000),
    "Trafford": (1300, 4200),
    "Wigan": (3500, 4200)
}

# Simple helper to simulate binary Yes/No with probability p for "Yes".
def yes_no(p):
    return "Yes" if random.random() < p else "No"

# Based on the rules implemented in the front end, these are the possible renovation scenarios we want to simulate.
RENOVATION_SCENARIOS = [
    ["Full renovation"],

    ["Bedroom", "Bathroom"],
    ["Bedroom", "Kitchen"],
    ["Bedroom", "Living room"],
    ["Bedroom", "Other/Custom"],

    ["Bathroom", "Kitchen"],
    ["Bathroom", "Living room"],
    ["Bathroom", "Other/Custom"],

    ["Living room", "Kitchen"],
    ["Living room", "Other/Custom"],
    
    ["Kitchen", "Other/Custom"],
    
    ["Living room", "Kitchen", "Other/Custom"],
    ["Bedroom", "Bathroom", "Kitchen"],
    ["Bedroom", "Bathroom", "Living room"],
    ["Bedroom", "Bathroom", "Other/Custom"]
]

EXTENSION_RULES = {
    "kitchen": [
        (0, 754, 108, 161),
        (755, 1076, 162, 215),
        (1078, 1507, 216, 269),
        (1508, float("inf"), 270, 377)
    ],
    
    "living room": [
        (0, 754, 129, 194),
        (755, 1076, 195, 269),
        (1078, 1507, 270, 377),
        (1508, float("inf"), 378, 538)
    ],

    "bathroom": [
        (0, 754, 43, 65),
        (755, 1076, 66, 86),
        (1078, 1507, 87, 108),
        (1508, float("inf"), 109, 151)
    ],

    "bedroom": [
        (0, 754, 86, 129),
        (755, 1076, 130, 172),
        (1078, 1507, 173, 237),
        (1508, float("inf"), 238, 322)
    ],
    
    "other/custom": [
        (0, 754, 65, 108),
        (755, 1076, 109, 151),
        (1078, 1507, 152, 215),
        (1508, float("inf"), 216, 301)
    ],
}


RENOVATION_RULES = {
    "kitchen": [
        (0, 754, 110, 160),
        (755, 1076, 161, 215),
        (1078, 1507, 216, 270),
        (1508, float("inf"), 271, 380)
    ],
    
    "living room": [
        (0, 754, 150, 220),
        (755, 1076, 221, 300),
        (1078, 1507, 301, 420),
        (1508, float("inf"), 421, 600)
    ],

    "bathroom": [
        (0, 754, 45, 65),
        (755, 1076, 66, 90),
        (1078, 1507, 91, 110),
        (1508, float("inf"), 111, 150)
    ],

    "bedroom": [
        (0, 754, 90, 130),
        (755, 1076, 131, 170),
        (1078, 1507, 171, 240),
        (1508, float("inf"), 241, 322)
    ],
    
    "other/custom": [
        (0, 754, 80, 130),
        (755, 1076, 131, 200),
        (1078, 1507, 221, 300),
        (1508, float("inf"), 301, 450)
    ],
}

def interpolate(val, low_x, high_x, low_y, high_y):
    ratio = (val - low_x) / (high_x - low_x)
    return low_y + ratio * (high_y - low_y)

def compute_sqft_to_add(room, property_size):
    rules = EXTENSION_RULES.get(room, EXTENSION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return high_y
            return interpolate(property_size, low_x, high_x, low_y, high_y)
        return 0
    
def compute_sqft_renovated_for_room(room, property_size):
    rules = RENOVATION_RULES.get(room, RENOVATION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return random.randint(low_y, high_y)
            return random.randint(
                int(interpolate(property_size, low_x, high_x, low_y, high_y)),
                high_y
            )

    return 0


rows = []

# Main generation loop: keep creating records until NUM_SAMPLES is reached.
while len(rows) < NUM_SAMPLES:

    # Choose a location and sample a property size within the location-specific range.
    location = random.choice(LOCATIONS)
    min_sqft, max_sqft = LOCATION_SIZE_RULES[location]
    property_size = random.randint(min_sqft, max_sqft)

    #randomly determine renovation type
    renovation_type = random.choice(RENOVATION_SCENARIOS)
    is_full = renovation_type == ["Full renovation"]

    #max extension size is 50% due to goverment guidelines
    max_extension_total = int(property_size * 0.50)

    if is_full:
        #for a full renovation you still need to find out the number of bedrooms and bathrooms 
        
        # scale bedrooms with property size
        # roughly 1 bedroom per 450 to 600 sqft
        bedrooms = max(1, int(property_size / random.uniform(450, 600)))

        # scale bathrooms with bedrooms
        # usually 1 bath per 1 to 2 bedrooms
        bathrooms = max(1, int(bedrooms / random.uniform(1.0, 2.0)))

        #used this rule in the real data so making it consistent here 
        renovated_sqft = property_size

        #compute extension sqft based on property size just like real data
        extension_sqft = compute_sqft_to_add("other/custom", property_size)

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

        #if extension done, the struct change should be yes
        if extension_sqft > 0:
            structural_changes = ["Yes"]
        else:
            structural_changes = ["No"]

    else:
        #num of bedrooms and bathrooms to renovate is based on property size
        bedrooms = max(1, int(property_size / random.uniform(450, 600)))
        bathrooms = max(1, int(bedrooms / random.uniform(1.0, 2.0)))

        #compute sqft renovated for each room based on property size just like real data
        sqft_renovated = {
            "bedrooms": [
                compute_sqft_renovated_for_room("bedroom", property_size)
                for _ in range(bedrooms)
            ],
            "bathrooms": [
                compute_sqft_renovated_for_room("bathroom", property_size)
                for _ in range(bathrooms)
            ],
            "other": {}
        }

        #compute sqft to add for each room based on property size just like real data
        sqft_to_add = {
            "bedrooms": [
                compute_sqft_to_add("bedroom", property_size)
                for _ in range(bedrooms)
            ],
            "bathrooms": [
                compute_sqft_to_add("bathroom", property_size)
                for _ in range(bathrooms)
            ],
            "other": {}
        }

        # For each specific non-bedroom/bathroom room in the renovation type, calculate the renovated sqft and extension sqft based on the property size using the same rules as the real data.
        for room in renovation_type:
            if room == "Kitchen":
                sqft_renovated["other"][room] = compute_sqft_renovated_for_room(room, property_size)
                sqft_to_add["other"][room] = compute_sqft_to_add(room, property_size)
            elif room == "Living room":
                sqft_renovated["other"][room] = compute_sqft_renovated_for_room(room, property_size)
                sqft_to_add["other"][room] = compute_sqft_to_add(room, property_size)
            elif room == "Other/Custom":
                sqft_renovated["other"][room] = compute_sqft_renovated_for_room(room, property_size)
                sqft_to_add["other"][room] = compute_sqft_to_add(room, property_size)

        # Assign material grades per item to vary quality across rooms.
        material_grade = {
            "bedrooms": [random.choice(MATERIAL_GRADES) for _ in range(bedrooms)],
            "bathrooms": [random.choice(MATERIAL_GRADES) for _ in range(bathrooms)],
            "other": {
                r: random.choice(MATERIAL_GRADES)
                for r in sqft_renovated["other"]
            }
        }

        total_items = bedrooms + bathrooms + len(sqft_renovated["other"])

        #if extension is done then structural change should be yes   
        structural_changes = []

        # bedrooms
        for sqft in sqft_to_add["bedrooms"]:
            structural_changes.append("Yes" if sqft > 0 else "No")

        # bathrooms
        for sqft in sqft_to_add["bathrooms"]:
            structural_changes.append("Yes" if sqft > 0 else "No")

        # other rooms
        for room in sqft_to_add["other"]:
            structural_changes.append(
                "Yes" if sqft_to_add["other"][room] > 0 else "No"
            )

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
