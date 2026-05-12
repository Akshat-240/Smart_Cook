"""
SmartCook — Data Storage
Handles reading and writing mess_attendance.csv using File I/O.
"""

import csv
from datetime import date
from pathlib import Path

from models.data_models import EventFlag, MealType, StudentLog

DATA_DIR        = Path(__file__).parent.parent / "data"
ATTENDANCE_FILE = DATA_DIR / "mess_attendance.csv"
FALLBACK_DATA_DIR = Path(__file__).parent.parent / "runtime_data"
FALLBACK_ATTENDANCE_FILE = FALLBACK_DATA_DIR / "mess_attendance.csv"

CSV_FIELDS = [
    "date", "meal_type", "actual_headcount",
    "cooked_for", "event_flag", "day_of_week",
    "waste_headcount", "waste_percentage",
]

COST_PER_PORTION_INR = 60


def _ensure_file() -> Path:
    for path in (ATTENDANCE_FILE, FALLBACK_ATTENDANCE_FILE):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                with open(path, "w", newline="") as f:
                    csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()
            else:
                with open(path, "a", newline=""):
                    pass
            return path
        except PermissionError:
            continue
    raise PermissionError("No writable attendance CSV location found")


def load_all_logs() -> list[StudentLog]:
    """Read all records from CSV and return as StudentLog objects."""
    attendance_file = _ensure_file()
    logs: list[StudentLog] = []
    with open(attendance_file, newline="") as f:
        for row in csv.DictReader(f):
            try:
                logs.append(StudentLog(
                    log_date         = date.fromisoformat(row["date"]),
                    meal_type        = MealType(row["meal_type"]),
                    actual_headcount = int(row["actual_headcount"]),
                    cooked_for       = int(row["cooked_for"]),
                    event_flag       = EventFlag(row["event_flag"]),
                ))
            except (ValueError, KeyError):
                continue   # skip malformed rows
    return logs


def append_log(log: StudentLog) -> None:
    """Append a single StudentLog to the CSV."""
    attendance_file = _ensure_file()
    with open(attendance_file, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(log.to_dict())


def log_exists(log_date: date, meal_type: MealType) -> bool:
    return any(
        l.log_date == log_date and l.meal_type == meal_type
        for l in load_all_logs()
    )


def delete_log(log_date: date, meal_type: MealType) -> bool:
    """Remove a specific entry. Returns True if deleted."""
    attendance_file = _ensure_file()
    logs = load_all_logs()
    filtered = [l for l in logs if not (l.log_date == log_date and l.meal_type == meal_type)]
    if len(filtered) == len(logs):
        return False
    with open(attendance_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for l in filtered:
            w.writerow(l.to_dict())
    return True


def get_waste_graph_data() -> list[dict]:
    """
    Returns per-session Actual Cooked vs. Optimal Required (in kg).
    Consumed by the frontend dual-line waste graph.
    """
    from models.data_models import PORTION_RATIOS
    result = []
    for log in load_all_logs():
        ratios = PORTION_RATIOS.get(log.meal_type, {})
        actual_kg   = round(sum(log.cooked_for       * q for q in ratios.values()), 2)
        optimal_kg  = round(sum(log.actual_headcount * q for q in ratios.values()), 2)
        result.append({
            "date":               log.log_date.isoformat(),
            "meal_type":          log.meal_type.value,
            "actual_cooked_kg":   actual_kg,
            "optimal_required_kg": optimal_kg,
            "waste_kg":           round(actual_kg - optimal_kg, 2),
        })
    return result


def get_savings_summary() -> dict:
    """Cumulative waste statistics and money wasted since deployment."""
    logs         = load_all_logs()
    total_waste  = sum(l.waste_headcount for l in logs)
    total_cooked = sum(l.cooked_for      for l in logs)
    total_actual = sum(l.actual_headcount for l in logs)
    waste_pct    = round((total_waste / total_cooked) * 100, 2) if total_cooked else 0.0
    return {
        "total_sessions_logged":  len(logs),
        "total_waste_portions":   total_waste,
        "total_cooked_portions":  total_cooked,
        "total_actual_portions":  total_actual,
        "overall_waste_percentage": waste_pct,
        "money_wasted_inr":       total_waste * COST_PER_PORTION_INR,
    }
