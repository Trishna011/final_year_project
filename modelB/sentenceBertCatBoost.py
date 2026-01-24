import re
import numpy as np
import pandas as pd
import spacy

df_real = pd.read_csv("processed_data/real_train_preprocessed.csv")


nlp = spacy.load("en_core_web_md")

STRUCTURAL_ANCHORS = [
    "extension", "extended", "loft", "conversion",
    "structural", "alteration"
]

STRUCTURAL_CONTEXT = [
    "planning", "permission", "rear", "side", "storey"
]

RENOVATION_ANCHORS = [
"kitchen",
"bathroom",
"bedroom",
"living",
"refurbish",
"renovate",
"modernise",
"upgrade"
]

RENOVATION_CONTEXT = [
"new",
"refitted",
"installed",
"updated",
"fully",
"recently"
]

RENOVATION_VERBS = [
    "fit", "fitted", "install", "installed",
    "upgrade", "upgraded", "refurbish", "refurbished",
    "renovate", "renovated", "modernise", "modernised"
]

ROOM_NOUNS = [
    "kitchen", "bathroom", "bedroom", "living", "lounge"
]
RENOVATION_ADJECTIVES = [
    "stylish",
    "modern",
    "contemporary",
    "luxurious",
    "sleek",
    "designer",
    "high spec",
    "integrated",
    "open plan"
]

QUALITY_CUES = [
"new",
"recent",
"recently",
"refitted",
"installed",
"upgraded",
"bespoke"
]

ANCHOR_STRUCTURAL_DOCS = [nlp(w) for w in STRUCTURAL_ANCHORS]
ANCHOR_RENOVATION_DOCS = [nlp(w) for w in RENOVATION_ANCHORS]
RENOVATION_VERB_DOCS = [nlp(w) for w in RENOVATION_VERBS]
ROOM_NOUN_DOCS = [nlp(w) for w in ROOM_NOUNS]
RENOVATION_ADJ_DOCS = [nlp(w) for w in RENOVATION_ADJECTIVES]
QUALITY_CUE_DOCS = [nlp(w) for w in QUALITY_CUES]

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

def embedding_structural_detector(text, similarity_threshold=0.65):
    doc = nlp(text)

    for token in doc:
        if not token.is_alpha:
            continue

        for anchor in ANCHOR_STRUCTURAL_DOCS:
            if token.similarity(anchor) >= similarity_threshold:
                window = doc[max(token.i - 5, 0): min(token.i + 6, len(doc))]
                window_text = window.text.lower()

                if any(c in window_text for c in STRUCTURAL_CONTEXT):
                    return 1

    return 0

def is_renovation_adjective(token, threshold=0.65):
    if token.pos_ != "ADJ":
        return False

    for adj in RENOVATION_ADJ_DOCS:
        if token.similarity(adj) >= threshold:
            return True

    return False

def is_quality_cue(token, threshold=0.65):
    if token.pos_ not in {"ADJ", "ADV", "VERB"}:
        return False

    for q in QUALITY_CUE_DOCS:
        if token.similarity(q) >= threshold:
            return True

    return False

def is_renovation_verb(token, threshold=0.65):
    for v in RENOVATION_VERB_DOCS:
        if token.similarity(v) >= threshold:
            return True
    return False


def is_room_noun(token, threshold=0.65):
    for r in ROOM_NOUN_DOCS:
        if token.similarity(r) >= threshold:
            return r.text
    return None


def embedding_renovation_detector(text, similarity_threshold=0.65):
    text = str(text).lower()
    doc = nlp(text)

    full_reno_phrases = [
        "fully refurbished",
        "fully renovated",
        "renovated throughout",
        "completely renovated",
        "full refurbishment",
        "entire property",
        "throughout the property"
    ]

    if any(p in text for p in full_reno_phrases):
        return "full renovation"

    found = set()

    # pass 1: explicit renovation actions
    for token in doc:
        if token.pos_ != "VERB":
            continue

        if not is_renovation_verb(token):
            continue

        window = doc[max(token.i - 5, 0): min(token.i + 6, len(doc))]

        for t in window:
            if t.pos_ == "NOUN":
                room = is_room_noun(t)
                if room:
                    if room in {"living", "lounge"}:
                        found.add("living room")
                    else:
                        found.add(room)

    # pass 2: implicit adjective based renovation with quality cue
    if not found:
        for token in doc:
            if not is_renovation_adjective(token):
                continue

            window = doc[max(token.i - 5, 0): min(token.i + 6, len(doc))]

            has_quality = any(is_quality_cue(t) for t in window)
            if not has_quality:
                continue

            window_tokens = [t.lemma_ for t in window]

            if "kitchen" in window_tokens:
                found.add("kitchen")
            if "bathroom" in window_tokens:
                found.add("bathroom")
            if "bedroom" in window_tokens:
                found.add("bedroom")
            if "living" in window_tokens or "lounge" in window_tokens:
                found.add("living room")


    if found:
        return list(found)

    return np.nan



def extract_structural_changes(text):
    # rule based first
    rule_keywords = [
        'extension', 'extended', 'loft conversion',
        'structural alteration', 'planning permission'
    ]
    if any(k in text for k in rule_keywords):
        return 1

    # embedding based fallback
    return embedding_structural_detector(text)


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
