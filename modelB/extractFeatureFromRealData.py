import re
import numpy as np
import pandas as pd
import spacy
from model.featureEngineering import reno_cost_for_real_data

# -----------------------------
# Load train or validation set
# -----------------------------

#df_real = pd.read_csv("processed_data/real_train_preprocessed2.csv")
#df_real = pd.read_csv("processed_data/real_val_preprocessed2.csv")
df_real = pd.read_csv("processed_data/real_test_preprocessed.csv")

# add unique id per row
df_real.insert(0, "id", range(1, len(df_real) + 1))

# Stores intermediate size calculations across rows
structural_property_sizes = []
renovation_room_sizes = []

# Load spaCy medium model for word embeddings and similarity checks
nlp = spacy.load("en_core_web_md")

# -----------------------------
# Keyword and semantic setup
# -----------------------

# Lemmas that indicate structural changes
STRUCTURAL_LEMMAS = {
    "extend",
    "convert",
    "conversion",
    "alter",
    "alteration",
    "structural"
}

# Explicit renovation phrases used in pattern matching
RENOVATION_PATTERNS = [
    r"\bnewly renovated\b",
    r"\brecently renovated\b",
    r"\brenovat\w*\b",
    r"\brefurbish\w*\b",
    r"\bnewly refurbished\b",
    r"\bcompletely refurbished\b",
    r"\bmoderni[sz]e\w*\b",
    r"\bmodernized\b",
    r"\bupgrade\w*\b",
    r"\brefit\w*\b",
    r"\bfinished to a high standard\b",
    r"\brecently upgraded\b",
    r"\bhigh\s+standard\b",
    r"\bimmaculate\b",
    r"\bpristine\b"
]

# Seed words representing renovation actions
RENOVATION_SEED_WORDS = [
    "renovated",
    "refurbished",
    "modernised",
    "upgraded",
    "refitted",
    "installed"
]

# Used to find similar words to renovation seeds to help find words other than in the list
RENOVATION_SEED_DOCS = [nlp(w) for w in RENOVATION_SEED_WORDS]

# Temporal words used to confirm recent renovation
RENOVATION_TEMPORAL_CUES = {
    "recent",
    "recently",
    "new",
    "newly",
    "just",
    "now"
}

ROOM_NOUNS = [
    "kitchen", "bathroom", "bedroom", "living", "lounge"
]

# Verbs that describe property state rather than renovation, which need to be ignored
STATE_VERBS = {
    "offer", "offers",
    "provide", "provides",
    "include", "includes",
    "feature", "features",
    "comprise", "comprises"
}

# Material keywords grouped by quality level
MATERIAL_SEEDS = {
    "budget-friendly": ["laminate", "vinyl", "carpet", "upvc", "acrylic", "mdf", "painted", "composite"],
    "mid-range": ["ceramic", "porcelain", "engineered", "granite", "steel", "timber", "glazed", "stoneware"],
    "high-end": ["hardwood", "marble", "quartz", "limestone", "slate", "aluminium", "brass", "bespoke"]
}

# Convert room and material words to spaCy docs to find similar words other than in the list
ROOM_NOUN_DOCS = [nlp(w) for w in ROOM_NOUNS]
MATERIAL_SEED_DOCS = {
    k: [nlp(w) for w in v]
    for k, v in MATERIAL_SEEDS.items()
}

# Price thresholds used to infer material quality
PRICE_HIGH = df_real["price"].quantile(0.75)
PRICE_LOW = df_real["price"].quantile(0.25)

# Used to calculate reasonable sqft to add or renovate based on property size and room type 
def interpolate(val, low_x, high_x, low_y, high_y):
    ratio = (val - low_x) / (high_x - low_x)
    return low_y + ratio * (high_y - low_y)

# Rules mapping reasonable extension sizes depending on property sizes for each room based on government guidelines and market research
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

# Rules mapping reasonable renovation sizes depending on property sizes for each room based on government guidelines and market research
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

# Estimate sqft to add based on the room and property size from real data
def compute_sqft_to_add(room, property_size):
    rules = EXTENSION_RULES.get(room, EXTENSION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return high_y
            return interpolate(property_size, low_x, high_x, low_y, high_y)

    return np.nan

# Estimate sqft renovated based on the room and property size from real data
def compute_sqft_renovated_for_room(room, property_size):
    rules = RENOVATION_RULES.get(room, RENOVATION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return high_y
            return interpolate(property_size, low_x, high_x, low_y, high_y)

    return 0

# -----------------------------
# Renovation detection helpers
# -----------------------------

# Check whether a token semantically represents renovation
def is_semantic_renovation_token(token, threshold=0.65):
    
    # only allow verbs and adjectives
    if token.pos_ not in {"VERB", "ADJ"}:
        return False

    # block generic state and marketing words
    if token.lemma_ in STATE_VERBS:
        return False

    # similarity check against renovation seeds
    for seed in RENOVATION_SEED_DOCS:
        if token.similarity(seed) >= threshold:
            return True

    return False

# Detect temporal words near a renovation token to confirm recent renovation
def has_temporal_cue(window):
    return any(t.lemma_ in RENOVATION_TEMPORAL_CUES for t in window)

# Identify whether a noun token represents a room based on similarity to room seed words
def is_room_noun(token, threshold=0.65):
    for r in ROOM_NOUN_DOCS:
        if token.similarity(r) >= threshold:
            return r.text
    return None

# Used to detect if a renovation token is detected and if so looks at context words to work out what room has been renovated
def embedding_renovation_detector(text, window_size=30):
    text = str(text).lower()
    doc = nlp(text)

    renovated_rooms = set()
    generic_renovation = False

    for token in doc:
        if not is_semantic_renovation_token(token):
            continue

        start = max(token.i - window_size, 0)
        end = min(token.i + window_size + 1, len(doc))
        window = doc[start:end]

        if not has_temporal_cue(window):
            continue

        room_found = False

        for t in window:
            if t.pos_ == "NOUN":
                room = is_room_noun(t)
                if room:
                    if room in {"living", "lounge"}:
                        room = "living room"
                    if room == "bath":
                        room = "bathroom"

                    renovated_rooms.add(room)
                    room_found = True

        if not room_found:
            generic_renovation = True

    if renovated_rooms:
        return list(renovated_rooms)

    if generic_renovation:
        return ["other/custom"]

    return np.nan

# -----------------------------
# Structural change detection
# -----------------------------

# Used to detect which room has been structually changed by looking at nearby nouns to the structural change token and checking if they are rooms or not. If no nearby nouns are found, we assume it is a custom/other structural change. We also add a window around the token to check for nearby nouns as sometimes the room may not be directly next to the structural change word.

def structural_changed_room(stuct_change_indicator, doc, row_id, window_size=2): 
    rooms = set() 
    start = max(stuct_change_indicator.i - window_size, 0) 
    end = min(stuct_change_indicator.i + window_size + 1, len(doc))
    window = doc[start:end] 
    found_noun = False
    
    for t in window:
        if t.pos_ == "NOUN":
            found_noun = True
            if t.lemma_ in ROOM_NOUNS:
                rooms.add(t.lemma_)
            else:
                rooms.add("other/custom")

    if not found_noun:
        rooms.add("other/custom")

    return list(rooms)

#Heuristic to check whether a token represents a structural event:
    #- adjectival past participles ("extended kitchen") or
    #- verbs in past/past-participle form ("was converted", "has been extended").

def is_actual_structural_event(token):
    # Case 1: past participle used adjectivally
    # "extended kitchen", "converted barn"
    if token.pos_ == "ADJ" and token.dep_ == "amod":
        return True

    # Case 2: past tense or past participle verb
    # "was extended", "has been converted"
    if token.pos_ == "VERB" and token.tag_ in {"VBD", "VBN"}:
        return True

    return False

# -----------------------------
# Material grade extraction
# -----------------------------

# Based on the price of the property, infer material grade
def price_material_signal(price):
    if price >= PRICE_HIGH:
        return {"high-end": 1.5, "mid-range": 0.5, "budget-friendly": 0}
    if price <= PRICE_LOW:
        return {"high-end": 0, "mid-range": 0.5, "budget-friendly": 1.5}
    return {"high-end": 0.3, "mid-range": 1.0, "budget-friendly": 0.3}


# Infer material quality using words and price
def extract_material_grade(text, price, threshold=0.75):
    text = str(text).lower()
    doc = nlp(text)

    scores = {
        "high-end": 0.0,
        "mid-range": 0.0,
        "budget-friendly": 0.0
    }

    # semantic contribution
    for token in doc:
        if token.pos_ not in {"ADJ", "ADV"}:
            continue
        for grade, seeds in MATERIAL_SEED_DOCS.items():
            for seed in seeds:
                if token.similarity(seed) >= threshold:
                    scores[grade] += 1.0

    # price contribution
    price_signal = price_material_signal(price)
    for grade in scores:
        scores[grade] += price_signal[grade]

    # no signal at all
    if max(scores.values()) == 0:
        return np.nan

    return max(scores, key=scores.get)


# Look for indicators of extensions and find whichg rooms have been extended and therefore strucutally changed
def extract_structural_changes(text, row_id, df, size_store):
    text = str(text).lower()
    doc = nlp(text)
    found = False

    extended_rooms = set()

    property_size = df.iloc[row_id]["property_size"]

    for token in doc:
        if not is_actual_structural_event(token):
            continue

        if not any(token.lower_.startswith(s) for s in STRUCTURAL_LEMMAS):
            continue

        #which room was extended 
        found = True
        detected_rooms = structural_changed_room(token, doc, row_id)
        for r in detected_rooms:
            extended_rooms.add(r)
            #extract property sizes of extended properties to calculate sqft to add
            size_store.append({
                "row_id": row_id+1,
                "room": r,
                "property_size": float(property_size)
            })
            
    #which room was extended
    if extended_rooms:
        df.at[row_id, "extended_rooms"] = ", ".join(sorted(extended_rooms))
    else:
        df.at[row_id, "extended_rooms"] = ""
        
    if found:
        return 1, list(extended_rooms) if extended_rooms else ["other/custom"]

    return 0, []


# Extract which type of room has been renovated based on explicit renovation keywords and semantic detection. We also use the number of rooms detected as renovated as a signal, where if 4 or more rooms are detected as renovated we classify it as a full renovation. We also store the detected renovation rooms and property size in a separate store to calculate sqft renovated later.
def extract_renovation_type(text, rooms, rowid, df, store):
    text = str(text).lower()
    renovation_rooms = set()

    if rooms:
        renovation_rooms.update(rooms)

    if re.search(r"\bmodernised throughout\b", text) or re.search(r"\bfully renovated\b", text):
        store.append({
            "row_id": rowid + 1,
            "rooms": ["full renovation"],
            "property_size": float(df.iloc[rowid]["property_size"])
        })
        return "full renovation"

    semantic_rooms = embedding_renovation_detector(text)
    if isinstance(semantic_rooms, list):
        renovation_rooms.update(semantic_rooms)

    if len(renovation_rooms) >= 4:
        store.append({
            "row_id": rowid + 1,
            "rooms": ["full renovation"],
            "property_size": float(df.iloc[rowid]["property_size"])
        })
        return "full renovation"

    if renovation_rooms:
        store.append({
            "row_id": rowid + 1,
            "rooms": list(renovation_rooms),
            "property_size": float(df.iloc[rowid]["property_size"])
        })
        return list(renovation_rooms)

    return np.nan

# Extract sqft to add based on the detected structural changes and property sizes from real data
def extract_sqft_to_add(structural_property_sizes):
    sqft_by_row = {}

    for record in structural_property_sizes:
        row_id = record["row_id"]
        room = record["room"]
        property_size = record["property_size"]

        sqft = compute_sqft_to_add(room, property_size)

        if np.isnan(sqft):
            continue

        if row_id not in sqft_by_row:
            sqft_by_row[row_id] = 0

        sqft_by_row[row_id] += sqft

    return sqft_by_row

# Extract sqft renovated based on the detected renovation rooms and property sizes from real data
def extract_sqft_renovated(renovation_room_sizes):
    sqft_by_row = {}

    for record in renovation_room_sizes:
        row_id = record["row_id"]
        rooms = record["rooms"]
        property_size = record["property_size"]

        if rooms == ["full renovation"]:
            sqft_by_row[row_id] = property_size
            continue

        total = 0
        for room in rooms:
            total += compute_sqft_renovated_for_room(room, property_size)

        sqft_by_row[row_id] = total

    return sqft_by_row

# -----------------------------
# Main feature extraction
# -----------------------------
def extract_features(df, description_col):
    df = df.copy()

    # Extract material grade
    df['material_grade'] = df.apply(
        lambda row: extract_material_grade(row[description_col], row["price"]),
        axis=1
    )
    
    # Find which rooms have been extended based on structural changes
    df["extended_rooms"] = ""
    df[['structural_changes', 'structural_rooms']] = df.apply(
            lambda row: pd.Series(
            extract_structural_changes(row[description_col], row.name, df, structural_property_sizes)
        ),
        axis=1
    )

    # APPLY renovation type PER ROW using rooms from same row
    df['type_of_renovation'] = df.apply(
        lambda row: extract_renovation_type(
            row[description_col],
            row['structural_rooms'],
            row.name,
            df, 
            renovation_room_sizes
        ),
        axis=1
    )

    # cleanup if you do not want to keep rooms
    df.drop(columns=['structural_rooms'], inplace=True)

    # Extract sqft to add
    sqft_lookup = extract_sqft_to_add(structural_property_sizes)

    df["sqft_to_add"] = df.index.map(
        lambda idx: sqft_lookup.get(idx + 1, 0)
    )

    # Extract sqft renovated
    sqft_reno = extract_sqft_renovated(renovation_room_sizes)

    df["sqft_renovated"] = df.index.map(
        lambda idx: sqft_reno.get(idx + 1, 0)
    )


    return df

def extract_reno_cost(
):
    # Call the renovation cost pipeline to estimate the renovation cost based on the real data using my Model 1
    df_with_cost = reno_cost_for_real_data()

    return df_with_cost


df_extracted = extract_features(
    df_real,
    description_col="description"
)

df_extracted[
    [
        "description",
        "num_of_bedrooms",
        "num_of_bathrooms",
        "material_grade",
        "structural_changes",
        "type_of_renovation",
        "property_size",
        "sqft_to_add",
        "sqft_renovated"
    ]
].head(10)


#df_extracted.to_csv("processed_data/real_with_extracted_features_synonyms2.csv", index=False)
#df_extracted.to_csv("processed_data/real_val_with_extracted_features_synonyms2.csv", index=False)
df_extracted.to_csv("processed_data/real_test_with_extracted_features_synonyms.csv", index=False)

df_final = extract_reno_cost()
