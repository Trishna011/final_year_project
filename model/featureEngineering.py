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


# #load the dataset from hugging face
# dataset = load_dataset("Trish101/property-dataset", split="train")
# df = dataset.to_pandas()
# #get rid of duplicate rows
# df = df.drop_duplicates()
# print("After removing duplicates:", df.shape)
# cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns

# #remove redundant columns
# df = df.drop(columns=["num_of_bedroom", "num_of_bathroom", "type_of_project"], errors="ignore")

# # Select only categorical or object/string columns
# cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
# print("Categorical columns:", list(cat_cols))

# for col in cat_cols:
#     df[col] = (
#         df[col]
#         .astype(str)
#         .str.strip()            # remove leading/trailing spaces
#         .str.lower()            # make all lowercase
#         .str.replace('-', ' ')  # unify hyphens and spaces
#     )

# cols_with_outliers = []
# #find the IQR and therefore the outliers
# numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns

# for col in numeric_cols:
#     Q1 = df[col].quantile(0.25)
#     Q3 = df[col].quantile(0.75)
#     IQR = Q3 - Q1
#     lower = Q1 - 1.5 * IQR
#     upper = Q3 + 1.5 * IQR
#     outliers = df[(df[col] < lower) | (df[col] > upper)]
    
#     if len(outliers) > 0:
#         cols_with_outliers.append(col)
    
#     print(f"{col}: {len(outliers)} outliers")

# #plot box plots for the numeric columns that have outliers and show the outliers
# plt.figure(figsize=(12, 6))
# sns.boxplot(data=df[cols_with_outliers])
# plt.title('Boxplots of Numeric Columns with Outliers')
# plt.xticks(rotation=45)
# plt.show()

# #k-fold cross validation
# #1. create cost bins - divides renovation costs into 5 equally populated bins eg bin0 -> lowest 20% costs, bin 1 -> next 20% of costs
# df["cost_bin"] = pd.qcut(df["renovation_cost"], q=5, labels=False)
# X = df.drop(columns=["renovation_cost", "cost_bin"])
# y = df["renovation_cost"]
# skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# #k-fold cross validation
# #1. create cost bins - divides renovation costs into 5 equally populated bins eg bin0 -> lowest 20% costs, bin 1 -> next 20% of costs
# df["cost_bin"] = pd.qcut(df["renovation_cost"], q=5, labels=False)
# X = df.drop(columns=["renovation_cost", "cost_bin"])
# y = df["renovation_cost"]
# skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# rmse_scorer = make_scorer(mean_squared_error, greater_is_better=False, squared=False)
# r2_scores = []
# mape_scores = []
# all_shap_summaries = []
# for fold, (train_idx, test_idx) in enumerate(skf.split(X, df["cost_bin"])):
#     X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
#     y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
#     y_train_log = np.log1p(y_train)
#     y_test_log = np.log1p(y_test)
    
#     numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns
#     X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    
# #     print(f"\n=== Fold {fold+1} ===")
# #     print("📊 Before scaling (first 5 rows):")
# #     print(X_train.head())
    
#     # Robust Scaler on numeric columns only
#     scaler = RobustScaler()
#     X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
#     X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])
    
    

#     #label encoding structural_changes
#     label_encoder = LabelEncoder()
#     X_train["structural_changes"] = label_encoder.fit_transform(X_train["structural_changes"])
#     X_test["structural_changes"] = label_encoder.transform(X_test["structural_changes"])
    
#     #frequency encode location
#     location_freq = X_train["Location"].value_counts(normalize=False)
#     X_train["Location"] = X_train["Location"].map(location_freq)
#     #for test data, unseen locations get frequency 0
#     X_test["Location"] = X_test["Location"].map(location_freq).fillna(0)
    
    
#     #target encode renovation_type
#     target_encoder = ce.TargetEncoder(cols=['renovation_type'])
#     X_train = target_encoder.fit_transform(X_train, y_train)
#     X_test = target_encoder.transform(X_test)
    
#     #ordinally encode material grade
#     grade_order = {
#         "budget friendly": 1,
#         "mid range": 2,
#         "high end": 3
#     }

#     # Map grades — unseen values become 0
#     X_train["material_grade"] = X_train["material_grade"].str.lower().map(grade_order).fillna(0)
#     X_test["material_grade"] = X_test["material_grade"].str.lower().map(grade_order).fillna(0)

# #     print("\n⚙️ After scaling (first 5 rows):")
# #     print(X_train.head())
    
#     #Add interaction terms
#     X_train["material_grade_x_labour_rate"] = X_train["material_grade"] * X_train["labour_rate_per_hr"]
#     X_test["material_grade_x_labour_rate"] = X_test["material_grade"] * X_test["labour_rate_per_hr"]

#     X_train["location_x_material_grade"] = X_train["Location"] * X_train["material_grade"]
#     X_test["location_x_material_grade"] = X_test["Location"] * X_test["material_grade"]
    
#     X_train = X_train.fillna(0)
#     X_test = X_test.fillna(0)

#     # === XGBoost model (no LASSO) ===
#     xgb_model = XGBRegressor(
#         objective="reg:squarederror",
#         tree_method="hist",
#         random_state=42,
#         device="cpu",
#         n_jobs=-1
#     )

#     param_dist = {
#         "n_estimators": [200, 400, 600],
#         "learning_rate": [0.01, 0.05, 0.1],
#         "max_depth": [3, 4, 5, 6],
#         "min_child_weight": [1, 3, 5],
#         "subsample": [0.6, 0.8, 1.0],
#         "colsample_bytree": [0.6, 0.8, 1.0],
#         "gamma": [0, 0.1, 0.3],
#         "reg_alpha": [0, 0.1, 0.5],
#         "reg_lambda": [1, 1.5, 2.0]
#     }

#     random_search = RandomizedSearchCV(
#         estimator=xgb_model,
#         param_distributions=param_dist,
#         n_iter=15,
#         scoring=rmse_scorer,
#         cv=3,
#         verbose=1,
#         n_jobs=-1,
#         random_state=42
#     )

#     random_search.fit(X_train, y_train_log)
#     best_model = random_search.best_estimator_
#     print("Best params:", random_search.best_params_)

#     # === Evaluation ===
#     y_pred = best_model.predict(X_test)
#     rmse = root_mean_squared_error(y_test_log, y_pred)
#     mae = mean_absolute_error(y_test_log, y_pred)
#     mse = mean_squared_error(y_test_log, y_pred)
#     r2 = r2_score(y_test_log, y_pred)
#     r2_scores.append(r2)
#     mape = np.mean(np.abs((y_test_log - y_pred) / y_test_log)) * 100
#     mape_scores.append(mape)

#     print(f"\nFold {fold+1} Metrics:")
#     print(f"  MAE : {mae:.4f}")
#     print(f"  RMSE: {rmse:.4f}")
#     print(f"  R²  : {r2:.4f}")
#     print(f"  MAPE: {mape:.2f}%")

#     # === SHAP Analysis ===
#     print("\n🔍 Calculating SHAP values...")
#     X_sample = X_test.sample(min(300, len(X_test)), random_state=42)

#     print("SHAP: checking dtypes in X_sample...")
#     print(X_sample.dtypes.value_counts())
#     non_numeric = X_sample.select_dtypes(exclude=[np.number]).columns
#     if len(non_numeric) > 0:
#         print("Non-numeric columns found:", list(non_numeric))


#     explainer = shap.Explainer(best_model.predict, X_sample)
#     shap_values = explainer(X_sample)
#     shap_importance = np.abs(shap_values.values).mean(axis=0)

#     shap_summary = (
#         pd.DataFrame({
#             "feature": X_sample.columns,
#             "mean_abs_shap": shap_importance
#         })
#         .sort_values("mean_abs_shap", ascending=False)
#         .reset_index(drop=True)
#     )
#     all_shap_summaries.append(shap_summary)

#     print("\n📊 Top SHAP features (Fold", fold + 1, ")")
#     for i, row in shap_summary.head(10).iterrows():
#         print(f"{i+1:2d}. {row['feature']:<35s} | Mean |SHAP|: {row['mean_abs_shap']:.5f}")

#     shap.summary_plot(shap_values.values, X_sample, show=False)
#     plt.title(f"SHAP Summary Plot — Fold {fold+1}")
#     plt.show()

# # === Aggregate Results ===
# overall_r2 = np.mean(r2_scores)
# overall_mape = np.mean(mape_scores)
# print(f"\nOverall R²: {overall_r2:.4f}")
# print(f"Overall MAPE: {overall_mape:.2f}%")

# print("\n====================")
# print("📊 AVERAGE SHAP VALUES ACROSS ALL FOLDS")
# print("====================")


# shap_df = pd.concat(all_shap_summaries)
# shap_mean = (
#     shap_df.groupby("feature", as_index=False)["mean_abs_shap"]
#     .mean()
#     .sort_values("mean_abs_shap", ascending=False)
#     .reset_index(drop=True)
# )

# # Optional pruning example (commented)
# # keep_features = list(shap_mean["feature"].head(40))
# # domain_keep = ["material_grade", "sqft_renovated", "labour_rate_per_hr", "structural_changes"]
# # selected_features = list(set(keep_features + domain_keep))

# # Print all features sorted by importance
# for i, row in shap_mean.iterrows():
#     print(f"{i+1:2d}. {row['feature']:<40s} | Mean |SHAP|: {row['mean_abs_shap']:.6f}")

# # Save SHAP
# shap_mean.to_csv("overall_shap_values.csv", index=False)
# print("\n✅ Saved to 'overall_shap_values.csv'")

# # Save assets for inference
# joblib.dump({
#     "model": best_model,
#     "scaler": scaler,
#     "label_encoder": label_encoder,
#     "target_encoder": target_encoder,
#     "location_freq": location_freq,
#     "grade_order": grade_order,
#     "selected_features": X_train.columns  # all features kept
# }, "renovation_model_assets.pkl")
# print("\n💾 Model and preprocessing assets saved.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_PATH = os.path.join(BASE_DIR, "renovation_model_assets.pkl")

assets = joblib.load(ASSET_PATH)
model = assets["model"]
scaler = assets["scaler"]
label_encoder = assets["label_encoder"]
target_encoder = assets["target_encoder"]
location_freq = assets["location_freq"]
grade_order = assets["grade_order"]
selected_features = assets["selected_features"]


def preprocess_input(df, scaler, label_encoder, target_encoder, location_freq, grade_order, selected_features):
    cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
    for col in cat_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()            # remove leading/trailing spaces
            .str.lower()            # make all lowercase
            .str.replace('-', ' ')  # unify hyphens and spaces
        )


    df["structural_changes"] = df["structural_changes"].replace({
        "Yes": True,
        "No": False
    }).astype(bool)

    #match scaling to sacling during training
    numeric_cols = list(scaler.feature_names_in_)
    df = df.reindex(columns=df.columns.union(numeric_cols, sort=False), fill_value=0)
    df[numeric_cols] = scaler.transform(df[numeric_cols])

    df["structural_changes"] = label_encoder.transform(df["structural_changes"])
    df["Location"] = df["Location"].map(location_freq).fillna(0)
    df = target_encoder.transform(df)
    df["material_grade"] = df["material_grade"].str.lower().map(grade_order).fillna(0)
    df["material_grade_x_labour_rate"] = df["material_grade"] * df["labour_rate_per_hr"]
    df["location_x_material_grade"] = df["Location"] * df["material_grade"]
    
    df = df.reindex(columns=selected_features, fill_value=0)
    return df


def prediction(input_json):
    input_df = pd.DataFrame([input_json])
    processed_df = preprocess_input(input_df, scaler, label_encoder, target_encoder, location_freq, grade_order, selected_features)
    y_pred_log = model.predict(processed_df)
    predicted_cost = np.expm1(y_pred_log)

    formatted_cost = f"{float(predicted_cost[0]):.2f}"
    
    return formatted_cost

def add_labour_rate(data):
    #avg labour rate of nearby companies
    avg_labour_rate = np.mean([26,27,27,27,26,26,26,26,27,26,26,15,26,26,27,40,27,26,26,26,26,27,26,26,26])

    base_rate = avg_labour_rate 
    grade = data.get("material_grade", "").lower()
    reno_type = data.get("renovation_type", "").lower()
    structural = data.get("structural_change", "").lower()


    # material grade adjustment
    if "high" in grade.lower():
        base_rate *= 1.35   
    elif "mid" in grade.lower():
        base_rate *= 1.0   
    elif "budget" in grade.lower():
        base_rate *= 0.85  

    # renovation type
    if "full" in reno_type:
        base_rate *= 1.4   # full renovation: +40%
    elif "kitchen" in reno_type:
        base_rate *= 1.25
    elif "bathroom" in reno_type:
        base_rate *= 1.3 
    elif "living room" in reno_type:
        base_rate *= 1.1
    elif "bedroom" in reno_type:
        base_rate *= 1.05
    elif "other" in reno_type:
        base_rate *= 1.0

    # Structural changes
    #the yes from front end needs to be converted to true 
    if structural == "true":
        base_rate *= 1.25

    data["labour_rate_per_hr"] = float(round(base_rate))
    return data

def expand_records(data):
    renovation_types = data.get("renovation_type", [])
    
    bedrooms_raw = data.get("bedrooms_to_reno")
    bathrooms_raw = data.get("bathrooms_to_reno")

    bedrooms = bedrooms_raw if isinstance(bedrooms_raw, int) else 0
    bathrooms = bathrooms_raw if isinstance(bathrooms_raw, int) else 0


    sqft_add = data.get("sqft_to_add", {})
    sqft_reno = data.get("sqft_renovated", {})

    material_raw = data.get("material_grade", {})
    struct_raw = data.get("structural_changes", [])

    # ---------- Convert material dict into lists ----------
    material = {
        "bedrooms": material_raw.get("bedrooms", []) if isinstance(material_raw, dict) else [],
        "bathrooms": material_raw.get("bathrooms", []) if isinstance(material_raw, dict) else [],
        "other": material_raw.get("other", {}) if isinstance(material_raw, dict) else {}
    }

    # ---------- Convert structural list → bedrooms/bathrooms/other chunks ----------
    total_units = bedrooms + bathrooms + len([t for t in renovation_types if t not in ["Bedroom","Bathroom"]])

    # pad list to avoid index error
    struct_raw = (struct_raw + [""] * total_units)[:total_units]

    struct = {
        "bedrooms": struct_raw[:bedrooms],
        "bathrooms": struct_raw[bedrooms:bedrooms+bathrooms],
        "other": struct_raw[bedrooms+bathrooms:]
    }

    base_shared = {
        "property_size": data.get("property_size"),
        "Location": data.get("Location"),
    }

    output = []

    # ---------- Bedrooms ----------
    for i in range(bedrooms):
        output.append({
            **base_shared,
            "renovation_type": "Bedroom",
            "sqft_to_add_to_property": sqft_add.get("bedrooms", [0]*bedrooms)[i] if i < len(sqft_add.get("bedrooms", [])) else 0,
            "sqft_renovated": sqft_reno.get("bedrooms", [0]*bedrooms)[i] if i < len(sqft_reno.get("bedrooms", [])) else 0,
            "material_grade": material["bedrooms"][i] if i < len(material["bedrooms"]) else "",
            "structural_changes": struct["bedrooms"][i] if i < len(struct["bedrooms"]) else "",
        })

    # ---------- Bathrooms ----------
    for i in range(bathrooms):
        output.append({
            **base_shared,
            "renovation_type": "Bathroom",
            "sqft_to_add_to_property": sqft_add.get("bathrooms", [0]*bathrooms)[i] if i < len(sqft_add.get("bathrooms", [])) else 0,
            "sqft_renovated": sqft_reno.get("bathrooms", [0]*bathrooms)[i] if i < len(sqft_reno.get("bathrooms", [])) else 0,
            "material_grade": material["bathrooms"][i] if i < len(material["bathrooms"]) else "",
            "structural_changes": struct["bathrooms"][i] if i < len(struct["bathrooms"]) else "",
        })


    # ---------- Other room types ----------
    other_rooms = [t for t in renovation_types if t not in ["Bedroom","Bathroom"]]

    for idx, room in enumerate(other_rooms):
        output.append({
            **base_shared,
            "renovation_type": room,
            "sqft_to_add_to_property": sqft_add.get("other",{}).get(room,0),
            "sqft_renovated": sqft_reno.get("other",{}).get(room,0),
            "material_grade": material["other"].get(room,""),
            "structural_changes": struct["other"][idx] if idx < len(struct["other"]) else "",
        })

    return output
