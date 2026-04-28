"""
SmartCook - Feature Engineering
Prepares features (X) and target (y) for the ML model.

Features used:
    - day_index      : 0 (Mon) to 6 (Sun)
    - meal_encoded   : 0=Breakfast, 1=Lunch, 2=Dinner
    - is_exam_period : 0 or 1
    - is_festival    : 0 or 1
    - is_weekend     : 0 or 1
    - is_holiday     : 0 or 1

Target:
    - headcount_actual : number of students who showed up
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader.load_kaggle import load_mess_data

FEATURE_COLS = [
    "day_index",
    "meal_encoded",
    "is_exam_period",
    "is_festival",
    "is_weekend",
    "is_holiday",
]

TARGET_COL = "headcount_actual"


def build_features(df):
    """
    Extract feature matrix X and target vector y from DataFrame.
    Returns: X (np.ndarray), y (np.ndarray), feature_names (list)
    """
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError("Missing columns in DataFrame: {}".format(missing))

    X = df[FEATURE_COLS].values.astype(float)
    y = df[TARGET_COL].values.astype(float)

    print("[features] X shape: {} | y shape: {}".format(X.shape, y.shape))
    print("[features] Target range: {} to {} students".format(int(y.min()), int(y.max())))
    return X, y, FEATURE_COLS


def get_feature_stats(df):
    """
    Returns summary statistics per meal type.
    """
    stats = {}
    for meal in ["Breakfast", "Lunch", "Dinner"]:
        subset = df[df["meal"] == meal]["headcount_actual"]
        stats[meal] = {
            "mean":   round(float(np.mean(subset)), 1),
            "median": round(float(np.median(subset)), 1),
            "std":    round(float(np.std(subset)), 1),
            "min":    int(np.min(subset)),
            "max":    int(np.max(subset)),
        }
    return stats


if __name__ == "__main__":
    df = load_mess_data()
    X, y, names = build_features(df)

    print("\n=== Feature Matrix (first 3 rows) ===")
    print(pd.DataFrame(X[:3], columns=names))

    print("\n=== Per-Meal Stats ===")
    stats = get_feature_stats(df)
    for meal, s in stats.items():
        print("{}: mean={}, std={}, range=[{}, {}]".format(
            meal, s["mean"], s["std"], s["min"], s["max"]
        ))
