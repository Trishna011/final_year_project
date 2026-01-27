from rich import print
import os
from openai import OpenAI  
from datasets import Dataset, DatasetDict, load_dataset
import json

topic = "Property Renovation Data"
n_subtopics = 10
n_questions = 100

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

TOPIC_GENERATION_PROMPT_TEMPLATE = """\
Given a topic, generate a list of {n_subtopics} renovation project types related to the topic.

The topic is: {topic}

The list must be without numbers, and without any description of the subtopics. 
The subtopics should be separated by a comma. There must be no other text than the list.
"""

def generate_subtopics(client, topic, n_subtopics):
    prompt = TOPIC_GENERATION_PROMPT_TEMPLATE.format(topic=topic, n_subtopics=n_subtopics)
    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[
            {"role": "user",
             "content": prompt}
        ],
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
    )
    return response

responses = generate_subtopics(client, topic=topic, n_subtopics=n_subtopics)
print(responses.choices[0].message.content)

QUESTION_PROMPT_TEMPLATE = """\
Given a renovation project type, generate {n_questions} renovation scenarios with detailed information.

Each scenario must include the following fields:
- property_size (sqft)
- num_of_bedroom
- num_of_bathroom
- Location (must be a real area within Greater Manchester, e.g., Manchester City Centre, Salford, Stockport, Bolton, Bury, Oldham, Rochdale, Tameside, Trafford, Wigan, Altrincham, Ashton-under-Lyne, Prestwich, Didsbury, Chorlton, Withington, Levenshulme, Sale, Stretford, or Cheadle)
- sqft_renovated
- sqft_to_add_to_property
- structural_changes? (Yes/No)
- type_of_project
- renovation_type (must be one of: Full renovation, Kitchen, Bathroom, Bedroom, Living room, Other)
- material_grade (must be one of: High-end, Mid-range, Budget-Friendly)
- labour_rate_per_hr
- renovation_cost

Provide each scenario as a JSON object on a new line.  
The output must not include numbering, bullet points, or extra commentary—just valid JSON objects separated by newlines.
"""

subtopic_list = responses.choices[0].message.content.split(",")
def generate_scenarios(client, sub_topic, n_questions):
    prompt = QUESTION_PROMPT_TEMPLATE.format(sub_topic=sub_topic, n_questions=n_questions)
    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        top_p=0.7,
        max_tokens=4096,
    )
    scenarios_text = response.choices[0].message.content.strip()
    print(f"Raw scenarios for {sub_topic}:\n{scenarios_text}\n")

    scenarios = []
    for line in scenarios_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            scenario = json.loads(line)
            scenarios.append(scenario)
        except json.JSONDecodeError:
            # fallback: print warning and skip invalid lines
            print(f"Warning: skipping invalid JSON line:\n{line}\n")
    return scenarios

# Collect all scenarios
BATCH_SIZE = 20
BATCHES = n_questions // BATCH_SIZE

all_scenarios = []

for subtopic in subtopic_list:
    print(f"\nGenerating scenarios for subtopic: {subtopic.strip()}")
    for batch in range(BATCHES):
        print(f"  Batch {batch + 1}/{BATCHES}")
        scenarios = generate_scenarios(client, subtopic.strip(), BATCH_SIZE)
        all_scenarios.extend(scenarios)
        print(f"  Added {len(scenarios)} scenarios (total so far: {len(all_scenarios)})")


# 3️⃣ Optional: Add a fixed sample manually (as per your example)
fixed_sample = {
    "property_size": 1200,
    "num_of_bedroom": 3,
    "num_of_bathroom": 2,
    "Location": "Didsbury",
    "sqft_renovated": 800,
    "sqft_to_add_to_property": 0,
    "structural_changes": False,
    "type_of_project": "Residential",
    "renovation_type": "Kitchen and Bathroom",
    "material_grade": "Mid-range",
    "Labour rate / hr": 40,
    "renovation_cost": 45000
}
all_scenarios.append(fixed_sample)

# 4️⃣ Save as JSONL
with open("synthetic_property_data.jsonl", "w") as f:
    for item in all_scenarios:
        f.write(json.dumps(item) + "\n")

# 5️⃣ Push to Hugging Face
dataset = Dataset.from_list(all_scenarios)
dataset_dict = DatasetDict({"train": dataset})
dataset_dict.push_to_hub("Trish101/property-dataset")

print(f"Generated {len(all_scenarios)} total scenarios.")