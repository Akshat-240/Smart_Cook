"""
SmartCook — Data Models
OOP classes to encapsulate meal sessions and attendance records.
No ML dependencies — prediction is handled by a separate service.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class MealType(str, Enum):
    BREAKFAST = "Breakfast"
    LUNCH     = "Lunch"
    DINNER    = "Dinner"


class EventFlag(str, Enum):
    NONE     = "none"
    EXAM     = "exam"
    FESTIVAL = "festival"
    WEEKEND  = "weekend"
    HOLIDAY  = "holiday"


# Cooking quantity ratios (kg or L) per student per meal
PORTION_RATIOS = {
    MealType.BREAKFAST: {"Poha/Upma": 0.15, "Milk": 0.25, "Bread": 0.10},
    MealType.LUNCH:     {"Rice": 0.20, "Dal": 0.13, "Sabzi": 0.11, "Roti": 0.08},
    MealType.DINNER:    {"Rice": 0.20, "Dal": 0.13, "Sabzi": 0.11, "Roti": 0.08},
}


@dataclass
class StudentLog:
    """A single meal-session attendance record logged by mess staff."""
    log_date:         date
    meal_type:        MealType
    actual_headcount: int
    cooked_for:       int          # portions actually prepared
    event_flag:       EventFlag = EventFlag.NONE

    # Auto-derived
    day_of_week:      int = field(init=False)   # 0=Mon ... 6=Sun
    waste_headcount:  int = field(init=False)   # cooked_for - actual (floored at 0)

    def __post_init__(self):
        self.day_of_week     = self.log_date.weekday()
        self.waste_headcount = max(0, self.cooked_for - self.actual_headcount)

    def waste_percentage(self) -> float:
        if self.cooked_for == 0:
            return 0.0
        return round((self.waste_headcount / self.cooked_for) * 100, 2)

    def to_dict(self) -> dict:
        return {
            "date":             self.log_date.isoformat(),
            "meal_type":        self.meal_type.value,
            "actual_headcount": self.actual_headcount,
            "cooked_for":       self.cooked_for,
            "event_flag":       self.event_flag.value,
            "day_of_week":      self.day_of_week,
            "waste_headcount":  self.waste_headcount,
            "waste_percentage": self.waste_percentage(),
        }


@dataclass
class CookingPlan:
    """
    Issued to the mess warden for a specific meal session.
    Receives predicted_headcount from the ML service (external).
    """
    session_date:        date
    meal_type:           MealType
    predicted_headcount: int
    event_flag:          EventFlag = EventFlag.NONE
    confidence_low:      Optional[int] = None
    confidence_high:     Optional[int] = None

    def cooking_quantities(self) -> dict[str, float]:
        return {
            item: round(self.predicted_headcount * qty, 2)
            for item, qty in PORTION_RATIOS.get(self.meal_type, {}).items()
        }

    def to_dict(self) -> dict:
        result = {
            "date":                self.session_date.isoformat(),
            "meal_type":           self.meal_type.value,
            "predicted_headcount": self.predicted_headcount,
            "event_flag":          self.event_flag.value,
            "cooking_quantities":  self.cooking_quantities(),
        }
        if self.confidence_low is not None and self.confidence_high is not None:
            result["confidence_interval"] = {
                "low":  self.confidence_low,
                "high": self.confidence_high,
            }
        return result