import os
import pandas as pd
from sklearn.model_selection import train_test_split,KFold
import numpy as np
import re
import spacy

folder_path = "../../model_2_real_data_3"

# Load spaCy English model for tokenisation and stopword removal
nlp = spacy.load("en_core_web_sm")

# Collect paths of all CSV files in the folder
all_files = [
    os.path.join(folder_path, f)
    for f in os.listdir(folder_path)
    if f.endswith(".csv")
]

dfs = []

# Read each CSV file and store as a DataFrame
for file in all_files:
    df_part = pd.read_csv(file)
    dfs.append(df_part)

# Combine all CSVs into one DataFrame
real_df = pd.concat(dfs, ignore_index=True)

print("Files loaded:", len(all_files))
print("Total rows:", real_df.shape)

#remove URL and extra column
real_df = real_df.drop(columns=["URL"], errors="ignore")
real_df = real_df.drop(columns=["Unnamed: 7"], errors="ignore")
real_df = real_df.drop(columns=["Unnamed: 8"], errors="ignore")

# Remove rows that are completely empty
real_df = real_df.dropna(how="all")

#remove duplicates
real_df = real_df.drop_duplicates()
print("After removing duplicates:", real_df.shape)

# Check for missing Location values
nan_locations = real_df[real_df["Location"].isna()]

print("Rows with NaN in Location:")
print(nan_locations)

# -----------------------------
# Price cleaning
# -----------------------------
def clean_price(x):
    # Convert price strings like "£250,000" to float
    if pd.isna(x):
        return np.nan
    x = str(x)
    x = x.replace("£", "").replace(",", "").strip()
    return float(x)

# Create numeric price column
real_df["price"] = real_df["Price"].apply(clean_price)
real_df = real_df.drop(columns=["Price"])


# -----------------------------
# Text cleaning and tokenisation
# -----------------------------
def clean_text(text):
    # Handle missing text
    if pd.isna(text):
        return ""
    # Basic normalisation
    text = str(text)
    text = text.lower()
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)

    # Tokenise with spaCy
    doc = nlp(text)

    # Keep useful tokens only
    tokens = [
        token.text
        for token in doc
            if (token.is_alpha or token.is_digit or token.like_num)
            and not token.is_stop
            ]

    return " ".join(tokens)

# Clean description text
real_df["description"] = real_df["Description"].apply(clean_text)
real_df = real_df.drop(columns=["Description"])

# -----------------------------
# TF IDF analysis
# -----------------------------
# Text input
X = real_df["description"].fillna("")

# Target variable
y = real_df["price"]

# Split into train and validation
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# Location target encoding
# -----------------------------
def split_encode(df,name):
    """
    Create train/validation CSVs with a target-encoded 'location' column.
    Procedure:
      - split 80/20 train/validation stratified by Location
      - perform KFold target-encoding on training data to avoid leakage
      - map full-training-location-means to validation set
      - save resulting CSVs under processed_data/
    """

    real_train_df, temp_df = train_test_split(
        df,
        test_size=0.3,
        random_state=42,
        stratify=df["Location"]
    )

    real_val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        random_state=42,
    )

    print("Train:", real_train_df.shape)
    print("Validation:", real_val_df.shape)
    print("Test:", test_df.shape)

    target_col = "price"
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    ## Initialise placeholder column for out-of-fold location encoding.
    real_train_df["location"] = 0.0

    # Global mean price
    global_mean = real_train_df[target_col].mean()

    # Out of fold encoding
    for train_idx, val_idx in kf.split(real_train_df):
        fold_train = real_train_df.iloc[train_idx]
        fold_val = real_train_df.iloc[val_idx]

        location_means = fold_train.groupby("Location")[target_col].mean()

        real_train_df.loc[fold_val.index, "location"] = (
            fold_val["Location"].map(location_means).fillna(global_mean)
        )
    
    # Encode validation using full training data
    location_means_full = real_train_df.groupby("Location")[target_col].mean()

    real_val_df["location"] = (
        real_val_df["Location"].map(location_means_full).fillna(global_mean)
    )

    test_df["location"] = (
        test_df["Location"].map(location_means_full).fillna(global_mean)
    )

    OUTPUT_DIR = "processed_data"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    train_path = os.path.join(OUTPUT_DIR, f"{name}_train_preprocessed.csv")
    val_path = os.path.join(OUTPUT_DIR, f"{name}_val_preprocessed.csv")
    test_path = os.path.join(OUTPUT_DIR, f"{name}_test_preprocessed.csv")

    real_train_df.to_csv(train_path, index=False)
    real_val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print("Saved real training data to:", train_path)
    print("Saved real validation data to:", val_path)
    print("Saved real test data to:", test_path)

split_encode(real_df, "real")