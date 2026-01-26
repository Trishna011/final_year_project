import re
import numpy as np
import pandas as pd
import spacy

df_real = pd.read_csv("processed_data/real_train_preprocessed.csv")


nlp = spacy.load("en_core_web_md")

STRUCTURAL_LEMMAS = {
    "extend",
    "extension",
    "convert",
    "conversion",
    "loft",
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



ROOM_NOUN_DOCS = [nlp(w) for w in ROOM_NOUNS]


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

def extract_material_grade(text):
    high = [
        'premium', 'luxury', 'high quality', 'top quality',
        'sleek', 'contemporary', 'designer', 'immaculately presented'
    ]
    low = [
        'dated', 'basic', 'tired', 'in need of modernisation',
        'requires renovation'
    ]

    if any(k in text for k in high):
        return 'high'
    if any(k in text for k in low):
        return 'low'
    return np.nan


def extract_structural_changes(text):
    text = str(text).lower()
    doc = nlp(text)

    for token in doc:
        if token.pos_ not in {"NOUN", "VERB"}:
            continue

        if token.lemma_ in STRUCTURAL_LEMMAS:
            return 1

    return 0

def extract_renovation_type(text):
    text = str(text).lower()

    if "modernised throughout" in text or "fully refurbished" in text:
        return "full renovation"

    return embedding_renovation_detector(text)



def extract_structured_features(df, description_col):
    df = df.copy()
    text = df[description_col].str.lower()

    df['num_of_bedrooms'] = text.apply(lambda t: int(re.search(r'(\d+)\s+bed', t).group(1)) if re.search(r'(\d+)\s+bed', t) else np.nan)
    df['num_of_bathrooms'] = text.apply(lambda t: int(re.search(r'(\d+)\s+bath', t).group(1)) if re.search(r'(\d+)\s+bath', t) else np.nan)

    df['material_grade'] = text.apply(extract_material_grade)
    df['structural_changes'] = text.apply(extract_structural_changes)
    df['type_of_renovation'] = text.apply(extract_renovation_type)

    # Not extractable reliably
    df['sqft_renovated'] = np.nan
    df['sqft_to_add'] = np.nan
    df['property_size'] = np.nan

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
        "type_of_renovation"
    ]
].head(10)


df_extracted.to_csv("processed_data/real_with_extracted_features_synonyms.csv", index=False)
