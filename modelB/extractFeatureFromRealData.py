import re
import numpy as np
import pandas as pd
import spacy

df_real = pd.read_csv("processed_data/real_val_preprocessed.csv")

# add unique id per row
df_real.insert(0, "id", range(1, len(df_real) + 1))

structural_property_sizes = []
renovation_room_sizes = []

nlp = spacy.load("en_core_web_md")

STRUCTURAL_LEMMAS = {
    "extend",
    "convert",
    "conversion",
    "alter",
    "alteration",
    "structural"
}


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

RENOVATION_SEED_WORDS = [
    "renovated",
    "refurbished",
    "modernised",
    "upgraded",
    "refitted",
    "installed"
]

RENOVATION_SEED_DOCS = [nlp(w) for w in RENOVATION_SEED_WORDS]

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

STATE_VERBS = {
    "offer", "offers",
    "provide", "provides",
    "include", "includes",
    "feature", "features",
    "comprise", "comprises"
}

MATERIAL_SEEDS = {
    "budget-friendly": ["laminate", "vinyl", "carpet", "upvc", "acrylic", "mdf", "painted", "composite"],
    "mid-range": ["ceramic", "porcelain", "engineered", "granite", "steel", "timber", "glazed", "stoneware"],
    "high-end": ["hardwood", "marble", "quartz", "limestone", "slate", "aluminium", "brass", "bespoke"]
}

ROOM_NOUN_DOCS = [nlp(w) for w in ROOM_NOUNS]
MATERIAL_SEED_DOCS = {
    k: [nlp(w) for w in v]
    for k, v in MATERIAL_SEEDS.items()
}

PRICE_HIGH = df_real["price"].quantile(0.75)
PRICE_LOW = df_real["price"].quantile(0.25)

def interpolate(val, low_x, high_x, low_y, high_y):
    ratio = (val - low_x) / (high_x - low_x)
    return low_y + ratio * (high_y - low_y)

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


def compute_sqft_to_add(room, property_size):
    rules = EXTENSION_RULES.get(room, EXTENSION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return high_y
            return interpolate(property_size, low_x, high_x, low_y, high_y)

    return np.nan
    
def compute_sqft_renovated_for_room(room, property_size):
    rules = RENOVATION_RULES.get(room, RENOVATION_RULES["other/custom"])

    for low_x, high_x, low_y, high_y in rules:
        if low_x <= property_size < high_x:
            if high_x == float("inf"):
                return high_y
            return interpolate(property_size, low_x, high_x, low_y, high_y)

    return 0

#RENOVATION TYPE HELPERS
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

def has_temporal_cue(window):
    return any(t.lemma_ in RENOVATION_TEMPORAL_CUES for t in window)

def is_room_noun(token, threshold=0.65):
    for r in ROOM_NOUN_DOCS:
        if token.similarity(r) >= threshold:
            return r.text
    return None

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

#STRUCTUAL CHANGE HELPERS

def structural_changed_room(stuct_change_indicator, doc, row_id, window_size=2): 
    rooms = set() 
    start = max(stuct_change_indicator.i - window_size, 0) 
    end = min(stuct_change_indicator.i + window_size + 1, len(doc))
    window = doc[start:end] 
    found_noun = False
    # for t in window:
    #     if t.pos_ == "NOUN": 
    #         lemma = t.lemma_ 
    #         if lemma in ROOM_NOUNS: 
    #             rooms.add(lemma) 
    #         else:
    #             rooms.add("other/custom")
    
    # return list(rooms)
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

#MATERIAL GRADE HELPER
def price_material_signal(price):
    if price >= PRICE_HIGH:
        return {"high-end": 1.5, "mid-range": 0.5, "budget-friendly": 0}
    if price <= PRICE_LOW:
        return {"high-end": 0, "mid-range": 0.5, "budget-friendly": 1.5}
    return {"high-end": 0.3, "mid-range": 1.0, "budget-friendly": 0.3}


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


# def extract_structural_changes(text, row_id):
#     text = str(text).lower()
#     doc = nlp(text)

#     for token in doc:

#         # must represent an actual event, not a possibility
#         if not is_actual_structural_event(token):
#             continue

#         #cannot compare the lemma of the token to STRUCTURAL_LEMMAS as spaCey treats 
#         #adjectives in the past as already lemmatised
#         if not any(token.lower_.startswith(s) for s in STRUCTURAL_LEMMAS):
#             continue

#         rooms = structural_changed_room(token, doc, row_id)
#         return 1, rooms if rooms else []

#     return 0, []

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
        
    if found:
        return 1, list(extended_rooms) if extended_rooms else ["other/custom"]

    return 0, []



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


def extract_structured_features(df, description_col):
    df = df.copy()

    df['material_grade'] = df.apply(
        lambda row: extract_material_grade(row[description_col], row["price"]),
        axis=1
    )
    
    # # APPLY structural extraction PER ROW
    # df[['structural_changes', 'structural_rooms']] = (
    #     text.apply(lambda t: pd.Series(extract_structural_changes(t)))
    # )

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

    #sqft to add
    sqft_lookup = extract_sqft_to_add(structural_property_sizes)

    df["sqft_to_add"] = df.index.map(
        lambda idx: sqft_lookup.get(idx + 1, 0)
    )

    #sqft to reno
    sqft_reno = extract_sqft_renovated(renovation_room_sizes)
    print(renovation_room_sizes)

    df["sqft_renovated"] = df.index.map(
        lambda idx: sqft_reno.get(idx + 1, 0)
    )


    return df


df_extracted = extract_structured_features(
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


df_extracted.to_csv("processed_data/real_val_with_extracted_features_synonyms.csv", index=False)
