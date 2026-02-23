import matplotlib.pyplot as plt
from openpyxl import Workbook
from modelB.catboost.catBoostFineTuned import run_test_predictions

y_test, test_preds, real_test = run_test_predictions()

# -------------------------
# Plot predicted vs acc cost graph
# -------------------------

# plt.figure(figsize=(8, 6))

# plt.scatter(y_test, test_preds)

# min_val = min(min(y_test), min(test_preds))
# max_val = max(max(y_test), max(test_preds))
# plt.plot([min_val, max_val], [min_val, max_val])

# plt.xlabel("Actual Post Renovation Value (£)")
# plt.ylabel("Predicted Post Renovation Value (£)")
# plt.title("Assessment of Predictive Performance for Post Renovation Property Valuation Model")

# plt.show()

# -------------------------
# Plot residual distribution hisogram
# -------------------------

# residuals = y_test - test_preds
# plt.figure(figsize=(8, 6))

# plt.hist(residuals, bins=15)

# plt.xlabel("Residual (£) = Actual Post Renovation Value − Predicted Post Renovation Value")
# plt.ylabel("Number of Properties")
# plt.title("Distribution of Prediction Errors for Post Renovation Property Value")

# plt.axvline(0, color="red")

# plt.show()

# -------------------------------------------
# Plot Residual vs Property Value
# -------------------------------------------

# plt.figure(figsize=(8, 6))

# plt.scatter(y_test, residuals)

# plt.axhline(0, color="red", linestyle="--", linewidth=2)

# plt.xlabel("Actual Post Renovation Value (£)")
# plt.ylabel("Residual (£) = Actual − Predicted")
# plt.title("Error Behaviour Across Property Value Range for Post Renovation Price Predictions")

# #plt.show()

# -------------------------------
# histogram of predicted_post_value - predicted_reno_cost
# -------------------------------
#predicted_uplift = test_preds - real_test["renovation_cost"]
# plt.figure(figsize=(8, 6))
# plt.hist(predicted_uplift, bins=15)
# plt.axvline(0, color="red", linestyle="--", linewidth=2)

# plt.xlabel("Predicted Net Value Gain (£)")
# plt.ylabel("Number of Properties")
# plt.title("Evaluation of Predicted Financial Return from Renovation Based on AI Valuation Models")

#plt.show()

# -------------------------------
# table of predicted_post_value - predicted_reno_cost
# -------------------------------

# summary_stats = {
# "Mean Predicted Gain (£)": np.mean(predicted_uplift),
# "Median Predicted Gain (£)": np.median(predicted_uplift),
# "Minimum Predicted Gain (£)": np.min(predicted_uplift),
# "Maximum Predicted Gain (£)": np.max(predicted_uplift),
# "Standard Deviation (£)": np.std(predicted_uplift),
# "Percentage Positive Gain (%)": np.mean(predicted_uplift > 0) * 100
# }

# summary_table = pd.DataFrame(summary_stats, index=["Value"])
# output_path = "../../graphs/predicted_uplift_summary.xlsx"

# summary_table.to_excel(output_path, index=True)
