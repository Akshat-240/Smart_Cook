"""
SmartCook — Flask REST API
Backend-only. Prediction is delegated to an external ML service.
Run with: python api/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from flask import Flask, jsonify, request

from models.data_models import CookingPlan, EventFlag, MealType, StudentLog, PORTION_RATIOS
from utils.calendar_intel import detect_event, upcoming_events
from utils.storage import (
    append_log, delete_log, get_savings_summary,
    get_waste_graph_data, load_all_logs, log_exists,
)

app = Flask(__name__)


# ── Index ──────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return jsonify({
        "project": "SmartCook — Campus Mess Food Waste Predictor",
        "status":  "running",
        "endpoints": {
            "health":           "GET  /health",
            "cooking_plan":     "POST /cooking-plan",
            "cooking_tomorrow": "GET  /cooking-plan/tomorrow",
            "logs_create":      "POST /logs",
            "logs_read":        "GET  /logs?from=&to=&meal=",
            "logs_delete":      "DELETE /logs?date=YYYY-MM-DD&meal=Dinner",
            "waste_graph":      "GET  /analytics/waste-graph",
            "savings":          "GET  /analytics/savings",
            "calendar_upcoming":"GET  /calendar/upcoming?days=7",
            "calendar_detect":  "GET  /calendar/detect?date=YYYY-MM-DD",
        }
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


def parse_date(s) -> date | None:
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def parse_meal(s) -> MealType | None:
    try:
        return MealType(s)
    except (ValueError, TypeError):
        return None


def parse_event(s) -> EventFlag | None:
    try:
        return EventFlag(s)
    except (ValueError, TypeError):
        return None


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# ── Cooking Plan ───────────────────────────────────────────────────────────────

@app.post("/cooking-plan")
def cooking_plan():
    """
    POST /cooking-plan
    The ML service calls this with its prediction; the backend validates,
    enriches with calendar context, and returns a warden-ready CookingPlan.

    Body:
    {
      "date":                "YYYY-MM-DD",
      "meal_type":           "Dinner",
      "predicted_headcount": 342,
      "confidence_low":      320,   ← optional
      "confidence_high":     365    ← optional
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return err("JSON body required")

    for field_name in ("date", "meal_type", "predicted_headcount"):
        if field_name not in data:
            return err(f"Missing field: '{field_name}'")

    session_date = parse_date(data["date"])
    if not session_date:
        return err(f"Invalid date: '{data['date']}'. Use YYYY-MM-DD.")

    meal = parse_meal(data["meal_type"])
    if not meal:
        return err(f"Invalid meal_type: '{data['meal_type']}'. Use Breakfast, Lunch, or Dinner.")

    try:
        headcount = int(data["predicted_headcount"])
    except (ValueError, TypeError):
        return err("predicted_headcount must be an integer")

    if headcount < 1:
        return err("predicted_headcount must be >= 1")

    conf_low  = data.get("confidence_low")
    conf_high = data.get("confidence_high")

    event_flag = detect_event(session_date)

    plan = CookingPlan(
        session_date        = session_date,
        meal_type           = meal,
        predicted_headcount = headcount,
        event_flag          = event_flag,
        confidence_low      = int(conf_low)  if conf_low  is not None else None,
        confidence_high     = int(conf_high) if conf_high is not None else None,
    )

    return jsonify(plan.to_dict()), 200


@app.get("/cooking-plan/tomorrow")
def cooking_plan_tomorrow():
    """
    GET /cooking-plan/tomorrow
    Returns calendar context for tomorrow's 3 meals so the ML service
    knows which event flags to apply when generating predictions.
    """
    tomorrow = date.today() + timedelta(days=1)
    event_flag = detect_event(tomorrow)
    return jsonify({
        "date":       tomorrow.isoformat(),
        "event_flag": event_flag.value,
        "meals": [
            {
                "meal_type":       meal.value,
                "portion_ratios":  {k: v for k, v in PORTION_RATIOS[meal].items()},
            }
            for meal in MealType
        ],
        "upcoming_events": upcoming_events(days=3),
    })


# ── Attendance Logging ─────────────────────────────────────────────────────────

@app.post("/logs")
def add_log():
    """
    POST /logs
    Staff record actual headcount after each meal.

    Body:
    {
      "date":             "YYYY-MM-DD",
      "meal_type":        "Dinner",
      "actual_headcount": 340,
      "cooked_for":       400,
      "event_flag":       "none"   ← optional, auto-detected if omitted
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return err("JSON body required")

    for field_name in ("date", "meal_type", "actual_headcount", "cooked_for"):
        if field_name not in data:
            return err(f"Missing field: '{field_name}'")

    log_date = parse_date(data["date"])
    if not log_date:
        return err(f"Invalid date: '{data['date']}'")

    meal = parse_meal(data["meal_type"])
    if not meal:
        return err(f"Invalid meal_type: '{data['meal_type']}'")

    try:
        actual = int(data["actual_headcount"])
        cooked = int(data["cooked_for"])
    except (ValueError, TypeError):
        return err("actual_headcount and cooked_for must be integers")

    if actual < 0 or cooked < 0:
        return err("Headcounts cannot be negative")

    event_raw = data.get("event_flag")
    event = parse_event(event_raw) if event_raw else detect_event(log_date)

    if log_exists(log_date, meal):
        return err(f"Record already exists for {log_date} {meal.value}. DELETE it first.", 409)

    log = StudentLog(log_date, meal, actual, cooked, event)
    append_log(log)
    return jsonify({"message": "Log recorded.", "record": log.to_dict()}), 201


@app.get("/logs")
def get_logs():
    """
    GET /logs?from=YYYY-MM-DD&to=YYYY-MM-DD&meal=Dinner
    All filters optional.
    """
    logs = load_all_logs()

    if raw := request.args.get("from"):
        if d := parse_date(raw):
            logs = [l for l in logs if l.log_date >= d]

    if raw := request.args.get("to"):
        if d := parse_date(raw):
            logs = [l for l in logs if l.log_date <= d]

    if raw := request.args.get("meal"):
        if m := parse_meal(raw):
            logs = [l for l in logs if l.meal_type == m]

    return jsonify({"count": len(logs), "logs": [l.to_dict() for l in logs]})


@app.delete("/logs")
def remove_log():
    """DELETE /logs?date=YYYY-MM-DD&meal=Dinner"""
    log_date = parse_date(request.args.get("date"))
    meal     = parse_meal(request.args.get("meal"))

    if not log_date or not meal:
        return err("`date` (YYYY-MM-DD) and `meal` query params are required")

    if not delete_log(log_date, meal):
        return err("No matching record found", 404)

    return jsonify({"message": f"Deleted {log_date} {meal.value}"})


# ── Analytics ──────────────────────────────────────────────────────────────────

@app.get("/analytics/waste-graph")
def waste_graph():
    """
    Actual Cooked vs. Optimal Required per session (kg).
    Powers the dual-line waste graph on the dashboard.
    """
    data = get_waste_graph_data()
    return jsonify({"data_points": len(data), "series": data})


@app.get("/analytics/savings")
def savings():
    """Cumulative waste stats and money wasted since deployment."""
    return jsonify(get_savings_summary())


# ── Calendar ───────────────────────────────────────────────────────────────────

@app.get("/calendar/upcoming")
def calendar_upcoming():
    """GET /calendar/upcoming?days=7"""
    try:
        days = max(1, min(int(request.args.get("days", 7)), 90))
    except ValueError:
        days = 7
    return jsonify({"events": upcoming_events(days=days)})


@app.get("/calendar/detect")
def calendar_detect():
    """GET /calendar/detect?date=YYYY-MM-DD"""
    d = parse_date(request.args.get("date"))
    if not d:
        return err("`date` (YYYY-MM-DD) required")
    return jsonify({"date": d.isoformat(), "event_flag": detect_event(d).value})


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)