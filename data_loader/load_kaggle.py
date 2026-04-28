"""
SmartCook - Data Loader
Loads and validates mess_attendance.csv (synthetic + real data).
"""

import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "smartcook_training_data.csv"


def load_mess_data(filepath=None):
    """
    Load mess attendance CSV and return a clean DataFrame.
    """
    if filepath is None:
        filepath = DATA_PATH
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            "Training data CSV not found at '{}'. "
            "Place/download 'smartcook_training_data.csv' in the project's "
            "'data/' directory, or pass a custom CSV path to "
            "load_mess_data(filepath=...).".format(filepath)
        )

    df = pd.read_csv(filepath)

    # Parse date
    df["date"] = pd.to_datetime(df["date"])

    # Encode meal type as integer
    meal_map = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
    df["meal_encoded"] = df["meal"].map(meal_map)

    # Combine event flags into single event_flag column
    def get_event(row):
        if row["is_festival"] == 1 or row["is_holiday"] == 1:
            return "festival"
        elif row["is_exam_period"] == 1:
            return "exam"
        elif row["is_weekend"] == 1:
            return "weekend"
        return "none"

    df["event_flag"] = df.apply(get_event, axis=1)

    # Drop rows with missing critical values
    df = df.dropna(subset=["headcount_actual", "meal_encoded", "day_index"])

    # Ensure correct types
    df["headcount_actual"]     = df["headcount_actual"].astype(int)
    df["actual_cooked_for"]    = df["actual_cooked_for"].astype(int)
    df["food_wasted_portions"] = df["food_wasted_portions"].astype(int)
    df["day_index"]            = df["day_index"].astype(int)

    print("[load_kaggle] Loaded {} rows | {} to {}".format(
        len(df),
        df["date"].min().date(),
        df["date"].max().date()
    ))
    return df


if __name__ == "__main__":
    df = load_mess_data()
    print(df.head())
    print("\nShape:", df.shape)
    print("\nMeal distribution:\n", df["meal"].value_counts())
    print("\nEvent distribution:\n", df["event_flag"].value_counts())
