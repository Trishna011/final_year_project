import pandas as pd
import os
import json
from pathlib import Path
import ast
import random
from rich import print
from datasets import Dataset, DatasetDict
from openai import OpenAI

# ------------------------------------------------------------------------------------
# Adds post-condition property descriptions using controlled, diverse LLM generation
# ------------------------------------------------------------------------------------

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# csv_path = (
#     PROJECT_ROOT
#     / "project"
#     / "synthetic_renovation_scenarios_with_pre_renovation_values.csv"
# )

csv_path = (
    PROJECT_ROOT.parent
    / "synthetic_renovation_scenarios_with_pre_renovation_values.csv"
)


df = pd.read_csv(csv_path)

# Normalise column names
df.columns = df.columns.str.strip().str.lower()

print("[green]Dataset loaded successfully[/green]")
print(df.head())

# -----------------------------
# Utilities
# -----------------------------
def parse_list_field(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return [value]
    return [str(value)]

# -----------------------------
# Narrative diversity controls
# -----------------------------
OPENING_MODES = [
    "Begin with a sentence focused on spatial arrangement without mentioning light.",
    "Begin with a sentence focused on circulation or movement through the home.",
    "Begin with a sentence focused on overall interior order or clarity.",
    "Begin with a sentence focused on how spaces relate to one another.",
    "Begin with a sentence focused on first impression without referencing entry or arrival."
]


VALUE_POSITIONING = [
    "functional and economical",
    "practical and considered",
    "composed and balanced",
    "refined and deliberate",
    "restrained and assured"
]

DETAIL_FOCUS = [
    "functional fixtures and usability",
    "layout efficiency and proportion",
    "material consistency and alignment",
    "spatial composition and flow",
    "select architectural or built-in elements"
]

ABSTRACTION_LEVEL = [
    "concrete and functional; avoid emotive or atmospheric language",
    "mostly concrete with limited abstraction (maximum one abstract sentence)",
    "balanced mix of concrete description and light abstraction",
    "predominantly abstract but grounded in physical detail"
]

SENTENCE_STYLE = [
    "short, direct sentences with clear structure",
    "mixed sentence length with a practical tone",
    "varied cadence with controlled complexity",
    "longer, flowing sentences used selectively"
]

# -----------------------------
# Cost-aware narrative control (NEW)
# -----------------------------
def cost_band_guidance(cost):
    if cost < 40000:
        return (
            "Emphasise practicality, efficiency, and straightforward use of space. "
            "Avoid complex spatial or design discussion."
        )
    elif cost < 75000:
        return (
            "Balance functional description with light reference to spatial planning "
            "and how rooms relate to one another."
        )
    else:
        return (
            "Reflect value through spatial arrangement, separation of functions, "
            "and deliberate layout decisions rather than adjectives."
        )

# -----------------------------
# Prompt construction
# -----------------------------
def build_prompt(row):
    renovation_focus = ", ".join(parse_list_field(row["renovation_type"]))
    structural = ", ".join(parse_list_field(row["structural_changes"]))

    opening_instruction = random.choice(OPENING_MODES)

    value_positioning = random.choice(VALUE_POSITIONING)
    detail_focus = random.choice(DETAIL_FOCUS)
    abstraction_level = random.choice(ABSTRACTION_LEVEL)
    sentence_style = random.choice(SENTENCE_STYLE)

    cost_guidance = cost_band_guidance(row["renovation_cost"])

    return f"""
Write a realistic UK estate-agent style property description describing the
current condition and presentation of the home.

OPENING INSTRUCTION:
{opening_instruction}

NARRATIVE CONTROLS (do not mention explicitly):
- Overall positioning: {value_positioning}
- Primary descriptive focus: {detail_focus}
- Abstraction guidance: {abstraction_level}
- Sentence construction: {sentence_style}
- Cost-based guidance: {cost_guidance}

STRICT RULES (must be followed exactly):
- Do NOT begin with phrases such as "This home", "This property", or similar
- Do NOT begin with common opening constructions such as:
  "Natural light", "Upon entering", "The principal living space",
  "The main living area", "The interior"
- Do NOT use estate-agent clichés including:
  "charming", "stunning", "beautiful", "bright and airy", "impressive"
- Do NOT explicitly state or imply that any renovation or works took place
- Do NOT use words such as "renovation", "renovated", "refurbished", "upgraded"
- Do NOT describe quality using labels such as
  "high-end", "luxury", "premium", "budget", or "affordable"
- Convey quality ONLY through specificity, proportion, restraint, and clarity
- Do NOT state or imply the total number of bedrooms or bathrooms
- Do NOT assume improved bedrooms/bathrooms represent the full accommodation
- Refer to sleeping and bathing spaces only in general terms
- Describe ONLY spaces that logically follow from the inputs
- Do NOT invent gardens, parking, transport links, schools, extensions, or land
- Do NOT mention prices, costs, square footage, or measurements
- Avoid sweeping lifestyle or emotional claims
- Do NOT reuse phrases or sentence structures across paragraphs

PARAGRAPH STRUCTURE (vary naturally):
- Paragraph 1: Layout, light, or internal organisation (choose one)
- Paragraph 2: ONE improved space chosen from: {renovation_focus}
- Paragraph 3 (optional): Overall coherence and presentation

PROPERTY CONTEXT (for grounding only, never state explicitly):
- Location: {row['location']}
- Home type: small-to-medium residential dwelling
- Improved spaces: {renovation_focus}
- Some bedrooms improved: {row['bedrooms_to_reno']}
- Some bathrooms improved: {row['bathrooms_to_reno']}
- Structural adjustment present: {structural}
- Overall condition: well-presented and ready for occupation

LANGUAGE & STYLE CONSTRAINTS:
- Present tense only
- UK residential marketing tone
- Avoid repetition within and across paragraphs
- Avoid mechanical feature listing
- Let value be inferred through control and precision
- Length: 2–3 paragraphs only
"""

# -----------------------------
# LLM generation
# -----------------------------
def generate_post_renovation_description(row):
    response = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {
                "role": "system",
                "content": "You are a UK residential property marketing copywriter."
            },
            {
                "role": "user",
                "content": build_prompt(row)
            }
        ],
        temperature=0.85,
        top_p=0.95,
        max_tokens=450,
    )
    description = response.choices[0].message.content.strip()
    print(description)
    return response.choices[0].message.content.strip()

print("[yellow]Generating post-condition descriptions...[/yellow]")

df["post_renovation_description"] = df.apply(
    generate_post_renovation_description,
    axis=1
)

print("[green]Post-condition descriptions generated[/green]")

# -----------------------------
# Save and push
# -----------------------------
def to_json_safe(x):
    if isinstance(x, (list, dict)):
        return json.dumps(x)
    return x

df = df.applymap(to_json_safe)

# output_csv = (
#     PROJECT_ROOT
#     / "project"
#     / "synthetic_renovation_scenarios_with_descriptions.csv"
# )

output_csv = (
    PROJECT_ROOT.parent
    / "synthetic_renovation_scenarios_with_descriptions.csv"
)


df.to_csv(output_csv, index=False)
print(f"[green]Saved local copy to {output_csv}[/green]")

dataset = Dataset.from_pandas(df, preserve_index=False)
dataset_dict = DatasetDict({"train": dataset})

HF_REPO_NAME = "Trish101/reno_details_dataset"

dataset_dict.push_to_hub(HF_REPO_NAME, private=True)

print(f"[bold green]Dataset pushed to Hugging Face:[/bold green] {HF_REPO_NAME}")
