import matplotlib.pyplot as plt
import matplotlib
from openpyxl import Workbook
from modelB.catboost.catBoostFineTuned import run_test_predictions
import shap
import matplotlib.gridspec as gridspec
import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy import stats
from sklearn.metrics import r2_score

y_test, test_preds, real_test, loaded_model, X_test, r2 = run_test_predictions()

# -------------------------
# Plot predicted vs acc cost graph
# -------------------------

# fig, ax = plt.subplots(figsize=(10, 6))

# # Scatter plot
# ax.scatter(y_test, test_preds, color="#2878B5", alpha=0.7, 
#            edgecolors="white", linewidth=0.5, zorder=3, label="Properties")

# # Perfect prediction line
# min_val = min(min(y_test), min(test_preds))
# max_val = max(max(y_test), max(test_preds))
# ax.plot([min_val, max_val], [min_val, max_val], 
#         color="red", linewidth=2, linestyle="--", label="Perfect Prediction", zorder=2)

# # ±10% confidence bands around the perfect prediction line
# x_line = np.linspace(min_val, max_val, 300)
# ax.fill_between(x_line, x_line * 0.9, x_line * 1.1, 
#                 alpha=0.1, color="green", label="±10% band")
# ax.fill_between(x_line, x_line * 0.8, x_line * 1.2, 
#                 alpha=0.07, color="orange", label="±20% band")

# # R² annotation
# r2 = r2_score(y_test, test_preds)
# ax.annotate(f"R² = {r2:.3f}",
#             xy=(0.05, 0.95), xycoords="axes fraction",
#             fontsize=12, va="top",
#             bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"))

# box_style = dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray")

# # Count points within bands
# within_10 = np.sum(np.abs(test_preds - y_test) / y_test < 0.10) / len(y_test) * 100
# within_20 = np.sum(np.abs(test_preds - y_test) / y_test < 0.20) / len(y_test) * 100

# stats_text = f"{within_10:.0f}% within ±10%\n{within_20:.0f}% within ±20%"
# ax.annotate(stats_text,
#             xy=(0.05, 0.82), xycoords="axes fraction",
#             fontsize=11, va="top",
#             bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"))

# ax.set_xlabel("Actual Post Renovation Value (£)", fontsize=12)
# ax.set_ylabel("Predicted Post Renovation Value (£)", fontsize=12)
# ax.set_title("Predicted vs Actual Post-Renovation Property Values", fontsize=14)
# ax.tick_params(labelsize=11)
# ax.legend(fontsize=10, loc="lower right")
# ax.grid(alpha=0.3)
# ax.spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)

# plt.tight_layout()
# plt.show()
# -------------------------
# Plot residual distribution graph
# -------------------------

# residuals = y_test - test_preds

# mean_res = np.mean(residuals)
# std_res = np.std(residuals)

# fig, ax = plt.subplots(figsize=(10, 6))

# # Use counts histogram but scale the normal curve to match
# n, bins, patches = ax.hist(residuals, bins=20,
#                             color="#2878B5", edgecolor="white", alpha=0.8,
#                             label="Residuals")

# # Scale normal curve to match count scale
# bin_width = bins[1] - bins[0]
# scale_factor = len(residuals) * bin_width  # this converts density → counts

# x = np.linspace(residuals.min(), residuals.max(), 300)
# normal_curve = stats.norm.pdf(x, mean_res, std_res) * scale_factor
# ax.plot(x, normal_curve, color="red", linewidth=2, label="Fitted Normal Distribution")
# # Zero reference line
# ax.axvline(0, color="black", linestyle="--", linewidth=1.2, alpha=0.6, label="Zero Error")

# # Mean and std annotation box
# stats_text = f"Mean:  £{mean_res:,.0f}\nStd Dev:  £{std_res:,.0f}"
# ax.annotate(stats_text,
#             xy=(0.97, 0.97), xycoords="axes fraction",
#             ha="right", va="top", fontsize=11,
#             bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"))

# ax.set_xlabel("Residual (£) = Actual Post Renovation Value − Predicted Post Renovation Value", fontsize=12)
# ax.set_ylabel("Number of Properties", fontsize=12)
# ax.set_title("Residual Distribution for Post-Renovation Property Valuation Model", fontsize=14)
# ax.tick_params(labelsize=11)
# ax.legend(fontsize=11)
# ax.grid(axis="y", alpha=0.3)
# ax.spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)

# plt.tight_layout()
# plt.show()

# -------------------------------------------
# Plot Residual vs Property Value
# -------------------------------------------
# residuals = y_test - test_preds
# fig, ax = plt.subplots(figsize=(10, 6))

# # Scatter plot
# ax.scatter(y_test, residuals, color="#2878B5", alpha=0.7, edgecolors="white", 
#            linewidth=0.5, zorder=3, label="Residuals")

# # Zero reference line
# ax.axhline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.8, label="Zero Error")

# # Reference bands ±£100k and ±£200k
# ax.axhspan(-100_000, 100_000, alpha=0.08, color="green", label="±£100k band")
# ax.axhspan(-200_000, 200_000, alpha=0.05, color="orange", label="±£200k band")

# # LOWESS smoothing line
# smoothed = lowess(residuals, y_test, frac=0.4)
# ax.plot(smoothed[:, 0], smoothed[:, 1], color="darkred", linewidth=2.5,
#         linestyle="-", label="LOWESS Trend", zorder=4)

# # Annotation explaining the LOWESS line
# ax.annotate("LOWESS trend shows how\nprediction error changes\nwith property value",
#             xy=(smoothed[-5, 0], smoothed[-5, 1]),
#             xytext=(smoothed[-5, 0] - 800_000, smoothed[-5, 1] + 150_000),
#             fontsize=10,
#             arrowprops=dict(arrowstyle="->", color="darkred"),
#             color="darkred",
#             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="darkred", alpha=0.8))

# ax.set_xlabel("Actual Post Renovation Value (£)", fontsize=12)
# ax.set_ylabel("Residual (£) = Actual − Predicted", fontsize=12)
# ax.set_title("Residual vs Actual Post-Renovation Property Value", fontsize=14)
# ax.tick_params(labelsize=11)
# ax.legend(fontsize=10, loc="upper left")
# ax.grid(axis="y", alpha=0.3)
# ax.spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)

# plt.tight_layout()
# plt.show()

# -------------------------------
# predicted_post_value - predicted_reno_cost
# -------------------------------
# predicted_uplift = test_preds - real_test["renovation_cost"]

# # Separate outlier (define threshold - adjust if needed)
# threshold = 2_000_000
# main_data = predicted_uplift[predicted_uplift <= threshold]
# outliers = predicted_uplift[predicted_uplift > threshold]

# median_val = predicted_uplift.median()


# # Create broken axis figure
# fig = plt.figure(figsize=(10, 6))

# gs = gridspec.GridSpec(1, 2, width_ratios=[4, 1], wspace=0.08)

# ax_main = fig.add_subplot(gs[0])
# ax_outlier = fig.add_subplot(gs[1])

# # --- Main axis ---
# ax_main.hist(main_data, bins=15, color="#2878B5", edgecolor="white")
# ax_main.axvline(median_val, color="red", linestyle="--", linewidth=1.5,
#                 label=f"Median: £{median_val:,.0f}")
# ax_main.legend(fontsize=11)
# ax_main.set_xlabel("Predicted Net Value Gain (£)", fontsize=12)
# ax_main.set_ylabel("Number of Properties", fontsize=12)
# ax_main.grid(axis="y", alpha=0.3)
# ax_main.spines["top"].set_visible(False)
# ax_main.spines["right"].set_visible(False)
# ax_main.set_title("...", fontsize=14)
# ax_main.tick_params(labelsize=11)
# ax_outlier.tick_params(labelsize=11)

# # n= annotation
# ax_main.annotate(f"n={len(predicted_uplift)} properties",
#                  xy=(0.97, 0.97), xycoords="axes fraction",
#                  ha="right", va="top", fontsize=11,
#                  bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray"))

# # --- Outlier axis ---
# for val in outliers:
#     ax_outlier.bar(0, 1, width=0.5, color="#2878B5", edgecolor="white")
#     ax_outlier.annotate(f"£{val/1e6:.2f}M", xy=(0, 1), xytext=(0, 1.15),
#                         ha="center", fontsize=10, color="black",
#                         arrowprops=dict(arrowstyle="->", color="gray"))

# ax_outlier.set_xlim(-0.5, 0.5)
# ax_outlier.set_ylim(0, ax_main.get_ylim()[1])
# ax_outlier.set_xticks([0])
# ax_outlier.set_xticklabels(["Outlier"], fontsize=10)
# ax_outlier.set_yticks([])
# ax_outlier.spines["top"].set_visible(False)
# ax_outlier.spines["right"].set_visible(False)
# ax_outlier.spines["left"].set_visible(False)
# ax_outlier.grid(axis="y", alpha=0.3)

# # Broken axis markers
# d = 0.015
# kwargs = dict(transform=fig.transFigure, color="k", clip_on=False, linewidth=1)
# # Get axis positions for break marks
# main_pos = ax_main.get_position()
# out_pos = ax_outlier.get_position()
# mid_y = main_pos.y0 + main_pos.height / 2
# for dy in [-0.02, 0.02]:
#     fig.add_artist(plt.Line2D([main_pos.x1 - 0.005, main_pos.x1 + 0.005],
#                                [mid_y + dy - 0.01, mid_y + dy + 0.01], **kwargs))
#     fig.add_artist(plt.Line2D([out_pos.x0 - 0.005, out_pos.x0 + 0.005],
#                                [mid_y + dy - 0.01, mid_y + dy + 0.01], **kwargs))

# fig.suptitle("Predicted Net Financial Return from Renovation",
#              fontsize=14)

# plt.tight_layout(rect=[0, 0, 1, 0.95])  
# plt.show()

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

# -------------------------------
# calculate shap values
# -------------------------------
# Set global font sizes before generating shap plots
matplotlib.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
})

explainer = shap.TreeExplainer(loaded_model)
shap_values = explainer.shap_values(X_test)

# --- Bar plot ---
fig, ax = plt.subplots(figsize=(10, 7))
shap.summary_plot(shap_values, X_test, 
                  plot_type="bar",
                  show=False,          # stops shap auto-displaying
                  color="#2878B5")     # consistent blue

ax = plt.gca()
ax.set_title("Mean Absolute SHAP Values — Feature Importance for\nPost Renovation Property Valuation Model", 
             fontsize=14, pad=15)
ax.set_xlabel("mean(|SHAP value|) (average impact on model output magnitude)", fontsize=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()

# --- Beeswarm plot ---
fig, ax = plt.subplots(figsize=(10, 7))
shap.summary_plot(shap_values, X_test,
                  show=False,
                  plot_size=None)     # prevents shap overriding our figsize

ax = plt.gca()
ax.set_title("SHAP Value Distribution by Feature — Post-Renovation Valuation Model", 
             fontsize=14, pad=15)
ax.set_xlabel("SHAP value (impact on model output)", fontsize=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()