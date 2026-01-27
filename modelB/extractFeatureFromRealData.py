import re
import numpy as np
import pandas as pd
import spacy

df_real = pd.read_csv("processed_data/real_train_preprocessed.csv")

# add unique id per row
df_real.insert(0, "id", range(1, len(df_real) + 1))


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
        else:
            print(token.lemma_, token.pos_)

        for grade, seeds in MATERIAL_SEED_DOCS.items():
            for seed in seeds:
                print(token.lemma_, seed, token.similarity(seed))
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

def extract_structural_changes(text, row_id):
    text = str(text).lower()
    doc = nlp(text)

    rooms = set()
    found = False

    for token in doc:
        if not is_actual_structural_event(token):
            continue

        if not any(token.lower_.startswith(s) for s in STRUCTURAL_LEMMAS):
            continue

        found = True
        detected_rooms = structural_changed_room(token, doc, row_id)
        for r in detected_rooms:
            rooms.add(r)

    if found:
        return 1, list(rooms) if rooms else ["other/custom"]

    return 0, []



def extract_renovation_type(text, rooms, rowid):
    text = str(text).lower()
    renovation_rooms = set()

    if rooms:
        renovation_rooms.update(rooms)

    if "modernised throughout" in text or "fully renovated" in text:
        return "full renovation"

    semantic_rooms = embedding_renovation_detector(text)
    if isinstance(semantic_rooms, list):
        renovation_rooms.update(semantic_rooms)

    if renovation_rooms:
        return list(renovation_rooms)

    return np.nan




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
            extract_structural_changes(row[description_col], row['id'])
        ),
        axis=1
    )

    # APPLY renovation type PER ROW using rooms from same row
    df['type_of_renovation'] = df.apply(
        lambda row: extract_renovation_type(
            row[description_col],
            row['structural_rooms'],
            row['id']
        ),
        axis=1
    )

    # cleanup if you do not want to keep rooms
    df.drop(columns=['structural_rooms'], inplace=True)

    # Not extractable reliably
    df['sqft_renovated'] = np.nan
    df['sqft_to_add'] = np.nan

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
        "property_size"
    ]
].head(10)


df_extracted.to_csv("processed_data/real_with_extracted_features_synonyms.csv", index=False)
