from datasets import load_dataset
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import RobustScaler, LabelEncoder, PolynomialFeatures
import category_encoders as ce
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.linear_model import LassoCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, make_scorer, root_mean_squared_error, mean_absolute_error,r2_score
import numpy as np
import shap, xgboost
import json
from mlxtend.plotting import heatmap
import joblib
import os


#load the dataset from hugging face
dataset = load_dataset("Trish101/property-dataset", split="train")
#load the dataset from hugging face
dataset = load_dataset("Trish101/property-dataset", split="train")
df = dataset.to_pandas()
#get rid of duplicate rows
df = df.drop_duplicates()
print("After removing duplicates:", df.shape)
cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
# Select only categorical or object/string columns
cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
print("Categorical columns:", list(cat_cols))
for col in cat_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()            # remove leading/trailing spaces
        .str.lower()            # make all lowercase
        .str.replace('-', ' ')  # unify hyphens and spaces
    )
for col in cat_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()            # remove leading/trailing spaces
        .str.lower()            # make all lowercase
        .str.replace('-', ' ')  # unify hyphens and spaces
    )

cols_with_outliers = []
#find the IQR and therefore the outliers
numeric_cols = df.select_dtypes(include='int64').columns

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df[(df[col] < lower) | (df[col] > upper)]
    
    if len(outliers) > 0:
        cols_with_outliers.append(col)
    
    print(f"{col}: {len(outliers)} outliers")

#plot box plots for the numeric columns that have outliers and show the outliers
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[cols_with_outliers])
plt.title('Boxplots of Numeric Columns with Outliers')
plt.xticks(rotation=45)
plt.show()

#k-fold cross validation
#1. create cost bins - divides renovation costs into 5 equally populated bins eg bin0 -> lowest 20% costs, bin 1 -> next 20% of costs
df["cost_bin"] = pd.qcut(df["renovation_cost"], q=5, labels=False)
X = df.drop(columns=["renovation_cost", "cost_bin"])
y = df["renovation_cost"]
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#k-fold cross validation
#1. create cost bins - divides renovation costs into 5 equally populated bins eg bin0 -> lowest 20% costs, bin 1 -> next 20% of costs
df["cost_bin"] = pd.qcut(df["renovation_cost"], q=5, labels=False)
X = df.drop(columns=["renovation_cost", "cost_bin"])
y = df["renovation_cost"]
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rmse_scorer = make_scorer(mean_squared_error, greater_is_better=False, squared=False)
r2_scores = []
mape_scores = []
for fold, (train_idx, test_idx) in enumerate(skf.split(X, df["cost_bin"])):
    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    y_train_log = np.log1p(y_train)
    y_test_log = np.log1p(y_test)
    
    numeric_cols = X_train.select_dtypes(include=["int64"]).columns
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    
#     print(f"\n=== Fold {fold+1} ===")
#     print("📊 Before scaling (first 5 rows):")
#     print(X_train.head())
    
    # Robust Scaler on numeric columns only
    scaler = RobustScaler()
    X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
    X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])
    

    #label encoding structural_changes
    label_encoder = LabelEncoder()
    X_train["structural_changes"] = label_encoder.fit_transform(X_train["structural_changes"])
    X_test["structural_changes"] = label_encoder.transform(X_test["structural_changes"])
    
    #frequency encode location
    location_freq = X_train["Location"].value_counts(normalize=False)
    X_train["Location"] = X_train["Location"].map(location_freq)
    #for test data, unseen locations get frequency 0
    X_test["Location"] = X_test["Location"].map(location_freq).fillna(0)
    
    #one hot encode types_of_project 
    X_train = pd.get_dummies(X_train, columns=["type_of_project"], prefix="project", drop_first=False)
    X_test = pd.get_dummies(X_test, columns=["type_of_project"], prefix="project", drop_first=False)
    
    #binary encode renovation_type
    binary_encoder = ce.BinaryEncoder(cols=['renovation_type'])
    X_train = binary_encoder.fit_transform(X_train)
    X_test = binary_encoder.transform(X_test)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    
    #ordinally encode material grade
    grade_order = {
        "budget friendly": 1,
        "mid range": 2,
        "high end": 3
    }

    # Map grades — unseen values become 0
    X_train["material_grade"] = X_train["material_grade"].str.lower().map(grade_order).fillna(0)
    X_test["material_grade"] = X_test["material_grade"].str.lower().map(grade_order).fillna(0)

#     print("\n⚙️ After scaling (first 5 rows):")
#     print(X_train.head())
    
    #Add interaction terms
    X_train["num_of_bedroom_x_labour_rate"] = X_train["num_of_bedroom"] * X_train["Labour rate / hr"]
    X_test["num_of_bedroom_x_labour_rate"] = X_test["num_of_bedroom"] * X_test["Labour rate / hr"]
    
    
    #LASSO feature selection
    lasso = LassoCV(cv = 5, random_state = 42)
    lasso.fit(X_train, y_train)
    
    #select only features with non 0 coefficients 
    selected_features = X_train.columns[lasso.coef_ != 0]
    print(f"Selected {len(selected_features)} features via LASSO")
    
    #reduce feature sets
    X_train_selected_features = X_train[selected_features]
    X_test_selected_features = X_test[selected_features]

    
    #Training the XGBoost model with my selected features + RandomSearchCV
    xgb_model = XGBRegressor(
        objective="reg:squarederror",
        tree_method="hist",
        random_state = 42,
        device="cpu",
        #data parallelism 
        n_jobs = 1
    )
    
    # --- Hyperparameter space for random search ---
    param_dist = {
        "n_estimators": [200, 400, 600],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 4, 5, 6],
        "min_child_weight": [1, 3, 5],
        "subsample": [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "gamma": [0, 0.1, 0.3],
        "reg_alpha": [0, 0.1, 0.5],
        "reg_lambda": [1, 1.5, 2.0]
    }
    
    random_search = RandomizedSearchCV(
        estimator=xgb_model,
        param_distributions=param_dist,
        n_iter=15,
        scoring=rmse_scorer,
        cv=3,                 # inner CV inside each outer fold
        verbose=1,
        n_jobs=-1,
        random_state=42
    )
    
    # --- Run tuning ---
    random_search.fit(X_train_selected_features, y_train_log)
    best_model = random_search.best_estimator_
    print("Best params:", random_search.best_params_)
    
    # --- Evaluate on test fold ---
    y_pred = best_model.predict(X_test_selected_features)
    rmse = root_mean_squared_error(y_test_log, y_pred)
    mae = mean_absolute_error(y_test_log, y_pred)
    mse = mean_squared_error(y_test_log, y_pred)
    r2 = r2_score(y_test_log, y_pred)
    r2_scores.append(r2)
    mape = np.mean(np.abs((y_test_log - y_pred) / y_test_log)) * 100
    mape_scores.append(mape)
    
    print("Average RMSE across folds:", np.mean(rmse))
    print(f"Fold {fold+1} Metrics:")
    print(f"  MAE : {mae:.4f}")
    print(f"  MSE : {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R²  : {r2:.4f}")
    print(f"  MAPE: {mape:.2f}%")
    
    
    #shap interpretation
    print("\n🔍 Calculating SHAP values...")

    # Take a sample of test data for speed and visualization
    X_sample = X_test_selected_features.sample(min(300, len(X_test_selected_features)), random_state=42)

    # Use model.predict as a callable — this avoids the internal JSON problem
    explainer = shap.Explainer(best_model.predict, X_sample)
    shap_values = explainer(X_sample)
    
    shap_importance = np.abs(shap_values.values).mean(axis=0)

    # Create a DataFrame of feature → impact magnitude
    shap_summary = pd.DataFrame({
        "feature": X_sample.columns,
        "mean_abs_shap": shap_importance
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

    # --- Display top features affecting the model ---
    print("\n📊 Top features impacting the model (Fold", fold + 1, ")")
    for i, row in shap_summary.head(15).iterrows():
        print(f"{i+1:2d}. {row['feature']:<40s} | Mean |SHAP| impact: {row['mean_abs_shap']:.5f}")


    # --- Visualize ---
    plt.title(f"SHAP Summary Plot — Fold {fold+1}")
    shap.summary_plot(shap_values.values, X_sample, show=False)
    plt.show()
    
    corr = df.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    heatmap(corr.values, row_names=corr.columns, column_names=corr.columns)
    plt.title("Feature Correlation Heatmap")
    plt.show()
    
overall_r2 = np.mean(r2_scores)
overall_mape = np.mean(mape_scores)

print(f"  Overall R²  : {overall_r2:.4f}")
print(f"  Overall MAPE  : {overall_mape:.4f}")
    
joblib.dump({
    "model": best_model,
    "scaler": scaler,
    "label_encoder": label_encoder,
    "binary_encoder": binary_encoder,
    "location_freq": location_freq,
    "grade_order": grade_order,
    "selected_features": selected_features
}, "renovation_model_assets.pkl")

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ASSET_PATH = os.path.join(BASE_DIR, "renovation_model_assets.pkl")

# assets = joblib.load(ASSET_PATH)
# model = assets["model"]
# scaler = assets["scaler"]
# label_encoder = assets["label_encoder"]
# binary_encoder = assets["binary_encoder"]
# location_freq = assets["location_freq"]
# grade_order = assets["grade_order"]
# selected_features = assets["selected_features"]


def preprocess_input(df, scaler, label_encoder, binary_encoder, location_freq, grade_order, selected_features):
    cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
    for col in cat_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()            # remove leading/trailing spaces
            .str.lower()            # make all lowercase
            .str.replace('-', ' ')  # unify hyphens and spaces
        )

    numeric_cols = df.select_dtypes(include=["int64"]).columns
    df[numeric_cols] = scaler.transform(df[numeric_cols])

    df["structural_changes"] = label_encoder.transform(df["structural_changes"])
    df["Location"] = df["Location"].map(location_freq).fillna(0)
    df = pd.get_dummies(df, columns=["type_of_project"], prefix="project", drop_first=False)
    df = binary_encoder.transform(df)
    df["material_grade"] = df["material_grade"].str.lower().map(grade_order).fillna(0)
    df["num_of_bedroom_x_labour_rate"] = df["num_of_bedroom"] * df["Labour rate / hr"]

    df = df.reindex(columns=selected_features, fill_value=0)

    return df


def prediction(input_json):
    input_df = pd.DataFrame([input_json])
    processed_df = preprocess_input(input_df, scaler, label_encoder, binary_encoder, location_freq, grade_order, selected_features)

    y_pred_log = model.predict(processed_df)
    predicted_cost = np.expm1(y_pred_log)
    
    return float(predicted_cost[0])

def add_labour_rate(data):
    #avg labour rate of nearby companies
    avg_labour_rate = np.mean([26,27,27,27,26,26,26,26,27,26,26,15,26,26,27,40,27,26,26,26,26,27,26,26,26])

    base_rate = avg_labour_rate
    grade = data.get("material_grade", "").lower()
    reno_type = data.get("renovation_type", "").lower()
    structural = data.get("structural_change", "").lower()


    # material grade adjustment
    if "high" in grade:
        base_rate += 10
    elif "mid" in grade:
        base_rate += 5

    # renovation type
    if "full" in reno_type:
        base_rate += 10
    elif "partial" in reno_type:
        base_rate += 5

    # Structural changes
    #the yes from front end needs to be converted to true 
    if structural == "true":
        base_rate += 10

    data["Labour rate / hr"] = int(round(base_rate))
    return data
    

