"""
SmartCook - Predictor
Loads trained model and returns headcount + cooking quantities for any date/meal.
This is what Aryan's Flask /cooking-plan endpoint will call.
"""

import numpy as np
import joblib
from pathlib import Path
from datetime import date
from utils.calendar_intel import is_exam_period, is_festival

MODEL_PATH  = Path(__file__).parent / "smartcook_model.pkl"
SCALER_PATH = Path(__file__).parent / "smartcook_scaler.pkl"

# Keep meal ordering in one place so feature encoding cannot drift from
# the meal definitions used by this predictor.
MEAL_TYPES = ("Breakfast", "Lunch", "Dinner")

# Portion ratios (kg per student)
PORTION_RATIOS = {
    "Breakfast": {"Poha/Upma": 0.15, "Milk": 0.25, "Bread": 0.10},
    "Lunch":     {"Rice": 0.20, "Dal": 0.13, "Sabzi": 0.11, "Roti": 0.08},
    "Dinner":    {"Rice": 0.20, "Dal": 0.13, "Sabzi": 0.11, "Roti": 0.08},
}

# Derive encoding from the single ordered meal definition above.
MEAL_ENCODING = {meal: index for index, meal in enumerate(MEAL_TYPES)}

COST_PER_PORTION_INR = 60


def _get_event_flags(target_date):
    """
    Returns is_exam_period, is_festival, is_weekend, is_holiday
    for a given date.
    """
    festival_flag = int(is_festival(target_date))
    is_holiday    = festival_flag
    is_exam       = int(is_exam_period(target_date))
    is_weekend    = int(target_date.weekday() >= 5)

    return {
        "is_exam_period": is_exam,
        "is_festival":    festival_flag,
        "is_weekend":     is_weekend,
        "is_holiday":     is_holiday,
    }


def predict(target_date, meal_type):
    """
    Predict headcount and cooking quantities for a given date + meal.

    Args:
        target_date : date object e.g. date(2026, 4, 30)
        meal_type   : "Breakfast", "Lunch", or "Dinner"

    Returns:
        dict with predicted_headcount, cooking_quantities, confidence_range
    """
    if meal_type not in MEAL_ENCODING:
        raise ValueError("meal_type must be Breakfast, Lunch or Dinner. Got: {}".format(meal_type))

    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        raise FileNotFoundError(
            "Model artifacts not found. Run model/train_model.py first."
        )

    # Load model + scaler
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    # Build feature vector
    flags = _get_event_flags(target_date)
    features = np.array([[
        target_date.weekday(),       # day_index (0=Mon to 6=Sun)
        MEAL_ENCODING[meal_type],    # meal_encoded
        flags["is_exam_period"],
        flags["is_festival"],
        flags["is_weekend"],
        flags["is_holiday"],
    ]])

    # Scale + predict
    features_scaled = scaler.transform(features)
    raw_prediction  = model.predict(features_scaled)[0]
    headcount       = max(1, int(round(raw_prediction)))

    # Confidence range +/- 10%
    conf_low  = max(1, int(headcount * 0.90))
    conf_high = int(headcount * 1.10)

    # Cooking quantities
    ratios = PORTION_RATIOS.get(meal_type, {})
    cooking_quantities = {
        item: round(headcount * qty, 2)
        for item, qty in ratios.items()
    }

    # Potential waste if warden cooks for conf_high
    overcooked          = conf_high - headcount
    potential_waste_inr = overcooked * COST_PER_PORTION_INR

    return {
        "date":                  target_date.isoformat(),
        "meal_type":             meal_type,
        "day_of_week":           target_date.strftime("%A"),
        "event_flags":           flags,
        "predicted_headcount":   headcount,
        "confidence_low":        conf_low,
        "confidence_high":       conf_high,
        "cooking_quantities_kg": cooking_quantities,
        "potential_waste_inr":   potential_waste_inr,
    }


if __name__ == "__main__":
    from datetime import date

    test_cases = [
        (date(2026, 4, 28), "Breakfast"),   # Tuesday normal
        (date(2026, 4, 28), "Lunch"),
        (date(2026, 4, 28), "Dinner"),
        (date(2026, 4, 26), "Lunch"),        # Sunday
        (date(2026, 4, 10), "Dinner"),       # Exam period
    ]

    for d, meal in test_cases:
        result = predict(d, meal)
        print("\n{} ({}) - {}".format(d, result["day_of_week"], meal))
        print("  Predicted headcount : {}".format(result["predicted_headcount"]))
        print("  Confidence range    : {} - {}".format(result["confidence_low"], result["confidence_high"]))
        print("  Cooking quantities  : {}".format(result["cooking_quantities_kg"]))
        print("  Potential waste     : Rs {}".format(result["potential_waste_inr"]))
