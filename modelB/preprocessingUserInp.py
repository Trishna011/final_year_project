import json
import ast
import pandas as pd

# load saved location target encoding
with open(
    "preprocessing_artifacts/location_target_encoding.json",
    "r",
    encoding="utf-8"
) as f:
    location_encoding = json.load(f)

#load feature columns
with open("preprocessing_artifacts/feature_columns.json") as f:
    FEATURE_COLS = json.load(f)


# ordinal encode material_grade
grade_map = {
    "budgetfriendly": 0,
    "midrange": 1,
    "highend": 2
}

def normalize_grade(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().replace("-", "").replace(" ", "")
    return text

#label encode struct changes
struct_map = {
    "Yes": 1,
    "No": 0
}

def encode_structural_changes_lists(value):
    # already a list from website input
    if isinstance(value, list):
        return [struct_map.get(v, 0) for v in value]

    # missing
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []

    # stringified list
    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            return []

        if isinstance(value, list):
            return [struct_map.get(v, 0) for v in value]

    return []

def encode_material_grade_lists(value):
    if pd.isna(value):
        return {}

    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            return {}

    if not isinstance(value, dict):
        return {}

    encoded = {}

    # bedrooms and bathrooms are lists of grades
    for room_type in ["bedrooms", "bathrooms"]:
        entries = value.get(room_type, [])
        if isinstance(entries, list):
            encoded_list = []
            for g in entries:
                key = normalize_grade(g)
                encoded_list.append(grade_map.get(key, 0))
            if encoded_list:
                encoded[room_type] = encoded_list

    # other is a dict of {space_name: grade_string}
    other_entries = value.get("other", {})
    if isinstance(other_entries, dict):
        other_encoded = {}
        for k, g in other_entries.items():
            key = normalize_grade(g)
            other_encoded[k] = grade_map.get(key, 0)
        if other_encoded:
            encoded["other"] = other_encoded

    return encoded

def encode(df):

    #structural encode
    df["structural_changes"] = df["structural_changes"].apply(encode_structural_changes_lists)

    #target encode location

    LOCATION_MAP = location_encoding["mapping"]
    GLOBAL_MEAN = location_encoding["global_mean"]

    # apply target encoding to website input
    df["location"] = (
        df["location"]
        .map(LOCATION_MAP)
        .fillna(GLOBAL_MEAN)
    )


    #encode material grade
    df["material_grade"] = df["material_grade"].apply(encode_material_grade_lists)


    # one hot encode renovation_type for now
    # replace dynamic category discovery with a fixed, complete schema
    fixed_types = [
        "Bathroom",
        "Bedroom",
        "Kitchen",
        "Living room",
        "Other/Custom",
        "Full renovation"
    ]

    for t in fixed_types:
        col_name = f"reno_{t.lower().replace(' ', '_').replace('/', '_')}"
        df[col_name] = df["renovation_type"].apply(lambda x: int(t in x))

    df = df.drop(columns=["renovation_type"])
    df = df.reindex(columns=FEATURE_COLS, fill_value=0)

    return df

def expand_df(df):
    # drop the specified columns
    df = df.drop(
        columns=[
            "renovation_type"
        ],
        errors="ignore"
    )

    #expand renovations

    output_rows = []

    for src_idx, r in df.iterrows():
        for _, r in df.iterrows():

            sqft_ren = r["sqft_renovated"]
            if isinstance(sqft_ren, str):
                sqft_ren = ast.literal_eval(sqft_ren)

            sqft_add = r["sqft_to_add"]
            if isinstance(sqft_add, str):
                sqft_add = ast.literal_eval(sqft_add)

            mat = r["material_grade"]
            if isinstance(mat, str):
                mat = ast.literal_eval(mat)

            struct = r["structural_changes"]
            if isinstance(struct, str):
                struct = ast.literal_eval(struct)

        struct = list(struct)
        struct_idx = 0


        base = {
            "property_size": r["property_size"],
            "location": r["location"],
            "renovation_cost": r["renovation_cost"],
        }
        # bedrooms
        if r["reno_bedroom"] == 1:
            for i, sqft in enumerate(sqft_ren.get("bedrooms", [])):
                output_rows.append({
                    **base,
                    "sqft_renovated": sqft,
                    "sqft_to_add": sqft_add["bedrooms"][i],
                    "material_grade": mat["bedrooms"][i],
                    "structural_change": struct[struct_idx],
                    "reno_bathroom": 0,
                    "reno_bedroom": 1,
                    "reno_kitchen": 0,
                    "reno_living_room": 0,
                    "reno_other_custom": 0,
                    "reno_full_renovation": 0
                })
                struct_idx += 1
        # bathrooms
        if r["reno_bathroom"] == 1:
            for i, sqft in enumerate(sqft_ren.get("bathrooms", [])):
                output_rows.append({
                    **base,
                    "sqft_renovated": sqft,
                    "sqft_to_add": sqft_add["bathrooms"][i],
                    "material_grade": mat["bathrooms"][i],
                    "structural_change": struct[struct_idx],
                    "reno_bathroom": 1,
                    "reno_bedroom": 0,
                    "reno_kitchen": 0,
                    "reno_living_room": 0,
                    "reno_other_custom": 0,
                    "reno_full_renovation": 0
                })
                struct_idx += 1
        # other spaces: kitchen, living room, custom, full reno
        for k, sqft in sqft_ren.get("other", {}).items():
            k_lower = k.lower()

            output_rows.append({
                **base,
                "sqft_renovated": sqft,
                "sqft_to_add": sqft_add["other"][k],
                "material_grade": mat["other"][k],
                "structural_change": struct[struct_idx],
                "reno_bathroom": 0,
                "reno_bedroom": 0,
                "reno_kitchen": int(k_lower == "kitchen"),
                "reno_living_room": int(k_lower == "living room"),
                "reno_other_custom": int(k_lower not in ["kitchen", "living room", "full renovation"]),
                "reno_full_renovation": int(k_lower == "full renovation"),
            })
            struct_idx += 1
    expanded_df = pd.DataFrame(output_rows)

    expanded_df = expanded_df.drop(
        columns=[
            "unit_index"
        ],
        errors="ignore"
    )

    print(expanded_df)

    return expanded_df
