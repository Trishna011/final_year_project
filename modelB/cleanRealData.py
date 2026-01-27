import os
import pandas as pd
from sklearn.model_selection import train_test_split,KFold
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
import spacy

folder_path = "../../model_2_real_data"
nlp = spacy.load("en_core_web_sm")

all_files = [
    os.path.join(folder_path, f)
    for f in os.listdir(folder_path)
    if f.endswith(".csv")
]

dfs = []

for file in all_files:
    df_part = pd.read_csv(file)
    dfs.append(df_part)

real_df = pd.concat(dfs, ignore_index=True)

print("Files loaded:", len(all_files))
print("Total rows:", real_df.shape)

#remove URL and extra column
real_df = real_df.drop(columns=["URL"], errors="ignore")
real_df = real_df.drop(columns=["Unnamed: 7"], errors="ignore")
real_df = real_df.drop(columns=["Unnamed: 8"], errors="ignore")
real_df = real_df.dropna(how="all")



#remove duplicates
real_df = real_df.drop_duplicates()
print("After removing duplicates:", real_df.shape)

nan_locations = real_df[real_df["Location"].isna()]

print("Rows with NaN in Location:")
print(nan_locations)

def clean_price(x):
    if pd.isna(x):
        return np.nan
    x = str(x)
    x = x.replace("£", "").replace(",", "").strip()
    return float(x)

real_df["price"] = real_df["Price"].apply(clean_price)
real_df = real_df.drop(columns=["Price"])


#lightly clean the description
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.lower()
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)

    doc = nlp(text)

    tokens = [
        token.text
        for token in doc
            if (token.is_alpha or token.is_digit or token.like_num)
            and not token.is_stop
            ]

    return " ".join(tokens)

real_df["description"] = real_df["Description"].apply(clean_text)
real_df = real_df.drop(columns=["Description"])

real_df_reno_removed = real_df.copy()

#remove the words that indicate renovation
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

def remove_renovation_words(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    for pattern in RENOVATION_PATTERNS:
        text = re.sub(pattern, "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

real_df_reno_removed["description"] = real_df_reno_removed["description"].apply(remove_renovation_words)

#test if there are any synonyms to remove
X = real_df_reno_removed["description"].fillna("")
y = real_df_reno_removed["price"]

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42
)

tfidf = TfidfVectorizer(
    min_df=5,
    ngram_range=(1,2),
    stop_words="english"
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_val_tfidf = tfidf.transform(X_val)

model = Ridge(alpha=1.0)
model.fit(X_train_tfidf, y_train)

feature_names = np.array(tfidf.get_feature_names_out())
coefs = model.coef_

top_pos = feature_names[np.argsort(coefs)[-30:]]
top_neg = feature_names[np.argsort(coefs)[:30]]

print("Top price increasing words:")
print(top_pos)

print("\nTop price decreasing words:")
print(top_neg)

[w for w in feature_names if "renovat" in w]
[w for w in feature_names if "refurb" in w]
[w for w in feature_names if "modern" in w]


def split_encode(df,name):
    #split data 20% valiation 80% training
    real_train_df, real_val_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["Location"]
    )

    print("Train:", real_train_df.shape)
    print("Validation:", real_val_df.shape)



    target_col = "price"
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    real_train_df["location"] = 0.0
    global_mean = real_train_df[target_col].mean()

    for train_idx, val_idx in kf.split(real_train_df):
        fold_train = real_train_df.iloc[train_idx]
        fold_val = real_train_df.iloc[val_idx]

        location_means = fold_train.groupby("Location")[target_col].mean()

        real_train_df.loc[fold_val.index, "location"] = (
            fold_val["Location"].map(location_means).fillna(global_mean)
        )

    location_means_full = real_train_df.groupby("Location")[target_col].mean()

    real_val_df["location"] = (
        real_val_df["Location"].map(location_means_full).fillna(global_mean)
    )
    real_train_df = real_train_df.drop(columns=["Location"])
    real_val_df = real_val_df.drop(columns=["Location"])


    print(real_train_df.head())
    print(real_val_df.head())

    OUTPUT_DIR = "processed_data"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    train_path = os.path.join(OUTPUT_DIR, f"{name}_train_preprocessed.csv")
    val_path = os.path.join(OUTPUT_DIR, f"{name}_val_preprocessed.csv")

    real_train_df.to_csv(train_path, index=False)
    real_val_df.to_csv(val_path, index=False)

    print("Saved real training data to:", train_path)
    print("Saved real validation data to:", val_path)

split_encode(real_df, "real")
split_encode(real_df_reno_removed, "real_df_reno_removed")