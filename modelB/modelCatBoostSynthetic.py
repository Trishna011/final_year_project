import pandas as pd
import ast

# load the dataframe
df = pd.read_csv("processed_data/synthetic_train_preprocessed.csv")

# drop the specified columns
df = df.drop(
    columns=[
        "post_renovation_description",
        "pre_renovation_cost",
        "renovation_type"
    ],
    errors="ignore"
)

#expand renovations

output_rows = []

for src_idx, r in df.iterrows():
    sqft_ren = ast.literal_eval(r["sqft_renovated"])
    sqft_add = ast.literal_eval(r["sqft_to_add"])
    mat = ast.literal_eval(r["material_grade"])
    struct = list(ast.literal_eval(r["structural_changes"]))

    struct_idx = 0

    base = {
        "source_row": src_idx,
        "property_size": r["property_size"],
        "location": r["location"],
        "renovation_cost": r["renovation_cost"],
        "post_renovation_value": r["post_renovation_value"]
    }
    # bedrooms
    if r["reno_bedroom"] == 1:
        for i, sqft in enumerate(sqft_ren.get("bedrooms", [])):
            output_rows.append({
                **base,
                "unit_type": "bedroom",
                "unit_index": i + 1,
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
                "unit_type": "bathroom",
                "unit_index": i + 1,
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
    
    # other spaces: kitchen, living room, custom
    for k, sqft in sqft_ren.get("other", {}).items():
        k_lower = k.lower()

        output_rows.append({
            **base,
            "unit_type": k_lower,
            "unit_index": 1,
            "sqft_renovated": sqft,
            "sqft_to_add": sqft_add["other"][k],
            "material_grade": mat["other"][k],
            "structural_change": struct[struct_idx],
            "reno_bathroom": 0,
            "reno_bedroom": 0,
            "reno_kitchen": int(k_lower == "kitchen"),
            "reno_living_room": int(k_lower == "livingroom"),
            "reno_other_custom": int(k_lower not in ["kitchen", "livingroom"]),
            "reno_full_renovation": 0
        })
        struct_idx += 1
    
    if r["reno_full_renovation"] == 1:
        output_rows.append({
            **base,
            "unit_type": "full_renovation",
            "unit_index": 1,
            "sqft_renovated": (
                sum(sqft_ren.get("bedrooms", [])) +
                sum(sqft_ren.get("bathrooms", [])) +
                sum(sqft_ren.get("other", {}).values())
            ),
            "sqft_to_add": (
                sum(sqft_add.get("bedrooms", [])) +
                sum(sqft_add.get("bathrooms", [])) +
                sum(sqft_add.get("other", {}).values())
            ),
            "material_grade": None,
            "structural_change": max(struct),
            "reno_bathroom": 0,
            "reno_bedroom": 0,
            "reno_kitchen": 0,
            "reno_living_room": 0,
            "reno_other_custom": 0,
            "reno_full_renovation": 1
        })

expanded_df = pd.DataFrame(output_rows)


output_path = "processed_data/synthetic_train_expanded.csv"

expanded_df.to_csv(output_path, index=False)

print("saved expanded dataframe to:", output_path)