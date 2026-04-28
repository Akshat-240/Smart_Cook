"""
SmartCook - Chart Generator
Generates the dual-line Actual Cooked vs Optimal Required waste graph.
Saves as PNG for the Flask dashboard to serve.
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader.load_kaggle import load_mess_data

OUTPUT_DIR = Path(__file__).parent.parent / "static" / "charts"

# Total kg per student per meal (sum of all item ratios)
TOTAL_RATIO = {
    "Breakfast": 0.50,
    "Lunch":     0.52,
    "Dinner":    0.52,
}


def generate_waste_graph(meal_type="Lunch", last_n_days=30, output_path=None):
    """
    Dual-line chart: Actual Cooked (kg) vs Optimal Required (kg).
    The gap between lines = food wasted.
    """
    df = load_mess_data()

    meal_df = (
        df[df["meal"] == meal_type]
        .sort_values("date")
        .tail(last_n_days)
        .copy()
    )

    if meal_df.empty:
        raise ValueError("No data found for meal_type={}".format(meal_type))

    ratio = TOTAL_RATIO.get(meal_type, 0.52)
    meal_df["actual_cooked_kg"]    = (meal_df["actual_cooked_for"] * ratio).round(2)
    meal_df["optimal_required_kg"] = (meal_df["headcount_actual"]  * ratio).round(2)
    meal_df["waste_kg"]            = (meal_df["actual_cooked_kg"] - meal_df["optimal_required_kg"]).round(2)

    dates      = meal_df["date"].values
    actual_kg  = meal_df["actual_cooked_kg"].values
    optimal_kg = meal_df["optimal_required_kg"].values
    waste_kg   = meal_df["waste_kg"].values

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    ax.plot(dates, actual_kg,  color="#E74C3C", linewidth=2,
            label="Actual Cooked (kg)", marker="o", markersize=3)
    ax.plot(dates, optimal_kg, color="#2ECC71", linewidth=2,
            label="Optimal Required (kg)", marker="o", markersize=3)

    ax.fill_between(dates, optimal_kg, actual_kg,
                    where=(actual_kg >= optimal_kg),
                    alpha=0.15, color="#E74C3C", label="Wasted Food")

    total_waste  = float(waste_kg[waste_kg > 0].sum())
    money_wasted = int(total_waste / ratio * 60)
    ax.annotate(
        "Total waste: {:.1f} kg  |  Rs {:,} wasted".format(total_waste, money_wasted),
        xy=(0.02, 0.95), xycoords="axes fraction",
        fontsize=9, color="#E74C3C",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", alpha=0.8)
    )

    ax.set_title("SmartCook - {} Waste Analysis (Last {} days)".format(meal_type, last_n_days),
                 color="white", fontsize=13, pad=12)
    ax.set_xlabel("Date", color="#aaaaaa", fontsize=10)
    ax.set_ylabel("Quantity (kg)", color="#aaaaaa", fontsize=10)
    ax.tick_params(colors="#aaaaaa")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45, ha="right")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")
    ax.grid(axis="y", color="#222222", linestyle="--", linewidth=0.7)
    ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=9)

    plt.tight_layout()

    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "waste_graph_{}.png".format(meal_type.lower())

    plt.savefig(str(output_path), dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("[chart] Saved -> {}".format(output_path))
    return output_path


def generate_all_charts():
    """Generate waste graphs for all three meal types."""
    paths = []
    for meal in ["Breakfast", "Lunch", "Dinner"]:
        try:
            p = generate_waste_graph(meal_type=meal, last_n_days=30)
            paths.append(p)
        except Exception as e:
            print("[chart] Warning: {} chart failed - {}".format(meal, e))
    return paths


if __name__ == "__main__":
    print("Generating SmartCook waste charts...")
    paths = generate_all_charts()
    print("\nDone! {} charts saved:".format(len(paths)))
    for p in paths:
        print("  {}".format(p))
