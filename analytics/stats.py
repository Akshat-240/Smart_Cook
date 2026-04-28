"""
SmartCook - Analytics & Statistics
NumPy-powered stats: moving averages, std deviation, waste summaries.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader.load_kaggle import load_mess_data


def moving_average(values, window=7):
    """
    Simple moving average over a window.
    Pads the start with NaN so output length matches input.
    """
    result = np.full(len(values), np.nan)
    for i in range(window - 1, len(values)):
        result[i] = np.mean(values[i - window + 1: i + 1])
    return result


def weighted_moving_average(values, window=7):
    """
    Weighted moving average - more recent days have higher weight.
    """
    weights = np.arange(1, window + 1, dtype=float)
    weights /= weights.sum()
    result = np.full(len(values), np.nan)
    for i in range(window - 1, len(values)):
        result[i] = np.dot(values[i - window + 1: i + 1], weights)
    return result


def compute_meal_stats(df):
    """
    Per meal-type x event_flag breakdown: mean, std, median headcount.
    """
    grouped = df.groupby(["meal", "event_flag"])["headcount_actual"].agg(
        mean=lambda x: round(float(np.mean(x)), 1),
        std=lambda x: round(float(np.std(x)), 1),
        median=lambda x: round(float(np.median(x)), 1),
        count="count",
    ).reset_index()
    return grouped


def compute_waste_stats(df):
    """
    Overall waste summary across the entire dataset.
    """
    total_cooked = int(df["actual_cooked_for"].sum())
    total_actual = int(df["headcount_actual"].sum())
    total_wasted = int(df["food_wasted_portions"].sum())
    waste_pct    = round((total_wasted / total_cooked) * 100, 2) if total_cooked else 0.0
    money_wasted = total_wasted * 60  # Rs 60 per portion

    return {
        "total_sessions":          len(df),
        "total_cooked":            total_cooked,
        "total_actual":            total_actual,
        "total_wasted":            total_wasted,
        "overall_waste_pct":       waste_pct,
        "money_wasted_inr":        money_wasted,
        "avg_waste_per_session":   round(total_wasted / len(df), 1),
    }


def day_of_week_pattern(df):
    """
    Average headcount per day of week per meal.
    """
    return df.groupby(["day_of_week", "meal"])["headcount_actual"].mean().round(1).reset_index()


if __name__ == "__main__":
    df = load_mess_data()

    print("=== Waste Summary ===")
    ws = compute_waste_stats(df)
    for k, v in ws.items():
        print("  {}: {}".format(k, v))

    print("\n=== Meal x Event Stats ===")
    print(compute_meal_stats(df).to_string(index=False))

    print("\n=== Day of Week Pattern ===")
    print(day_of_week_pattern(df).to_string(index=False))

    breakfast = df[df["meal"] == "Breakfast"]["headcount_actual"].values
    ma  = moving_average(breakfast, window=7)
    wma = weighted_moving_average(breakfast, window=7)
    print("\n7-day MA  (last 5): {}".format(np.round(ma[-5:], 1)))
    print("7-day WMA (last 5): {}".format(np.round(wma[-5:], 1)))
