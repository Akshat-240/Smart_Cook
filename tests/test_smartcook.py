import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import date, timedelta

from models.data_models import EventFlag, MealType, StudentLog, CookingPlan, PORTION_RATIOS
from utils.calendar_intel import detect_event, upcoming_events


# ── StudentLog ─────────────────────────────────────────────────────────────────

class TestStudentLog:
    def test_waste_headcount_calculated(self):
        log = StudentLog(date(2025, 10, 1), MealType.DINNER, 300, 400)
        assert log.waste_headcount == 100

    def test_waste_headcount_no_negative(self):
        log = StudentLog(date(2025, 10, 1), MealType.LUNCH, 400, 350)
        assert log.waste_headcount == 0

    def test_waste_percentage(self):
        log = StudentLog(date(2025, 10, 1), MealType.BREAKFAST, 200, 250)
        assert log.waste_percentage() == 20.0

    def test_waste_percentage_zero_cooked(self):
        log = StudentLog(date(2025, 10, 1), MealType.LUNCH, 0, 0)
        assert log.waste_percentage() == 0.0

    def test_day_of_week_set(self):
        monday = date(2025, 10, 6)
        log = StudentLog(monday, MealType.LUNCH, 300, 300)
        assert log.day_of_week == 0

    def test_to_dict_keys(self):
        log = StudentLog(date(2025, 10, 1), MealType.DINNER, 300, 360)
        d = log.to_dict()
        for key in ["date", "meal_type", "actual_headcount", "cooked_for",
                    "event_flag", "day_of_week", "waste_headcount", "waste_percentage"]:
            assert key in d

    def test_event_flag_default_none(self):
        log = StudentLog(date(2025, 10, 1), MealType.LUNCH, 300, 300)
        assert log.event_flag == EventFlag.NONE


# ── CookingPlan ────────────────────────────────────────────────────────────────

class TestCookingPlan:
    def test_cooking_quantities_dinner(self):
        plan = CookingPlan(date(2025, 10, 1), MealType.DINNER, 400)
        qty = plan.cooking_quantities()
        assert qty["Rice"] == round(400 * 0.20, 2)
        assert qty["Dal"]  == round(400 * 0.13, 2)

    def test_cooking_quantities_breakfast(self):
        plan = CookingPlan(date(2025, 10, 1), MealType.BREAKFAST, 200)
        assert "Milk" in plan.cooking_quantities()

    def test_to_dict_no_ci_when_omitted(self):
        plan = CookingPlan(date(2025, 10, 1), MealType.LUNCH, 300)
        d = plan.to_dict()
        assert "confidence_interval" not in d

    def test_to_dict_has_ci_when_set(self):
        plan = CookingPlan(date(2025, 10, 1), MealType.LUNCH, 300,
                           confidence_low=280, confidence_high=320)
        d = plan.to_dict()
        assert d["confidence_interval"] == {"low": 280, "high": 320}

    def test_to_dict_has_cooking_quantities(self):
        plan = CookingPlan(date(2025, 10, 1), MealType.DINNER, 350)
        d = plan.to_dict()
        assert "cooking_quantities" in d
        assert "predicted_headcount" in d


# ── Calendar Intelligence ──────────────────────────────────────────────────────

class TestCalendarIntel:
    def test_festival_detection(self):
        assert detect_event(date(2025, 10, 21)) == EventFlag.FESTIVAL  # Diwali

    def test_weekend_detection(self):
        saturday = date(2025, 10, 4)
        assert detect_event(saturday) == EventFlag.WEEKEND

    def test_upcoming_events_structure(self):
        events = upcoming_events(days=30)
        assert isinstance(events, list)
        for e in events:
            assert "date" in e and "event" in e

    def test_festival_beats_exam(self):
        from utils import calendar_intel
        original = calendar_intel.FESTIVAL_DATES.copy()
        exam_date = calendar_intel.EXAM_PERIODS[0][0]
        calendar_intel.FESTIVAL_DATES.add(exam_date)
        assert detect_event(exam_date) == EventFlag.FESTIVAL
        calendar_intel.FESTIVAL_DATES = original


# ── Storage ────────────────────────────────────────────────────────────────────

class TestStorage:
    @pytest.fixture(autouse=True)
    def tmp_csv(self, tmp_path, monkeypatch):
        import utils.storage as storage
        monkeypatch.setattr(storage, "ATTENDANCE_FILE", tmp_path / "attendance.csv")
        storage._ensure_file()

    def test_append_and_load(self):
        from utils.storage import append_log, load_all_logs
        log = StudentLog(date(2025, 11, 1), MealType.DINNER, 300, 360)
        append_log(log)
        logs = load_all_logs()
        assert len(logs) == 1
        assert logs[0].actual_headcount == 300

    def test_log_exists(self):
        from utils.storage import append_log, log_exists
        log = StudentLog(date(2025, 11, 2), MealType.LUNCH, 280, 320)
        assert not log_exists(date(2025, 11, 2), MealType.LUNCH)
        append_log(log)
        assert log_exists(date(2025, 11, 2), MealType.LUNCH)

    def test_delete_log(self):
        from utils.storage import append_log, delete_log, load_all_logs
        log = StudentLog(date(2025, 11, 3), MealType.BREAKFAST, 150, 180)
        append_log(log)
        assert delete_log(date(2025, 11, 3), MealType.BREAKFAST)
        assert len(load_all_logs()) == 0

    def test_delete_nonexistent_returns_false(self):
        from utils.storage import delete_log
        assert not delete_log(date(2099, 1, 1), MealType.DINNER)

    def test_savings_summary_keys(self):
        from utils.storage import get_savings_summary
        s = get_savings_summary()
        for key in ["total_sessions_logged", "total_waste_portions",
                    "money_wasted_inr", "overall_waste_percentage"]:
            assert key in s

    def test_waste_graph_data(self):
        from utils.storage import append_log, get_waste_graph_data
        log = StudentLog(date(2025, 11, 4), MealType.DINNER, 300, 360)
        append_log(log)
        data = get_waste_graph_data()
        assert len(data) == 1
        assert data[0]["waste_kg"] >= 0
        assert "actual_cooked_kg" in data[0]
        assert "optimal_required_kg" in data[0]


# ── Flask API ──────────────────────────────────────────────────────────────────

class TestFlaskAPI:
    @pytest.fixture(autouse=True)
    def setup_client(self, tmp_path, monkeypatch):
        import utils.storage as storage
        monkeypatch.setattr(storage, "ATTENDANCE_FILE", tmp_path / "attendance.csv")
        storage._ensure_file()
        import api.app as app_module

        def fake_predict(target_date, meal_type):
            lookup = {
                "Breakfast": (150, 135, 165),
                "Lunch": (180, 162, 198),
                "Dinner": (342, 320, 365),
            }
            headcount, low, high = lookup[meal_type]
            return {
                "date": target_date.isoformat(),
                "meal_type": meal_type,
                "day_of_week": target_date.strftime("%A"),
                "event_flags": {},
                "predicted_headcount": headcount,
                "confidence_low": low,
                "confidence_high": high,
                "cooking_quantities_kg": {},
                "potential_waste_inr": (high - headcount) * 60,
            }

        monkeypatch.setattr(app_module, "predict_headcount", fake_predict)
        app = app_module.app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"

    # Cooking Plan
    def test_cooking_plan_valid(self):
        r = self.client.post("/cooking-plan", json={
            "date": "2026-06-10",
            "meal_type": "Dinner",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["predicted_headcount"] == 342
        assert "cooking_quantities" in data
        assert "event_flag" in data
        assert data["confidence_interval"] == {"low": 320, "high": 365}

    def test_predict_route_valid(self):
        r = self.client.get("/predict?date=2026-06-10&meal=Dinner")
        assert r.status_code == 200
        data = r.get_json()
        assert data["predicted_headcount"] == 342
        assert data["meal_type"] == "Dinner"

    def test_predict_route_missing_date(self):
        r = self.client.get("/predict?meal=Dinner")
        assert r.status_code == 400

    def test_cooking_plan_auto_event_flag(self):
        r = self.client.post("/cooking-plan", json={
            "date": "2025-10-21",   # Diwali
            "meal_type": "Lunch",
        })
        assert r.status_code == 200
        assert r.get_json()["event_flag"] == "festival"

    def test_cooking_plan_missing_field(self):
        r = self.client.post("/cooking-plan", json={
            "date": "2026-06-10",
            # missing meal_type
        })
        assert r.status_code == 400

    def test_cooking_plan_predictor_unavailable(self, monkeypatch):
        import api.app as app_module

        def broken_predict(*_args, **_kwargs):
            raise FileNotFoundError("Model artifacts not found. Run model/train_model.py first.")

        monkeypatch.setattr(app_module, "predict_headcount", broken_predict)
        r = self.client.post("/cooking-plan", json={
            "date": "2026-06-10",
            "meal_type": "Lunch",
        })
        assert r.status_code == 503

    def test_cooking_plan_tomorrow(self):
        r = self.client.get("/cooking-plan/tomorrow")
        assert r.status_code == 200
        data = r.get_json()
        assert "date" in data and "event_flag" in data
        assert len(data["meals"]) == 3

    # Logs
    def test_post_log(self):
        r = self.client.post("/logs", json={
            "date": "2030-01-01",
            "meal_type": "Dinner",
            "actual_headcount": 310,
            "cooked_for": 380,
        })
        assert r.status_code == 201
        assert r.get_json()["record"]["actual_headcount"] == 310

    def test_post_log_auto_event_flag(self):
        r = self.client.post("/logs", json={
            "date": "2025-10-21",
            "meal_type": "Dinner",
            "actual_headcount": 170,
            "cooked_for": 250,
        })
        assert r.status_code == 201
        assert r.get_json()["record"]["event_flag"] == "festival"

    def test_post_duplicate_log(self):
        payload = {"date": "2030-02-01", "meal_type": "Lunch",
                   "actual_headcount": 280, "cooked_for": 330}
        self.client.post("/logs", json=payload)
        assert self.client.post("/logs", json=payload).status_code == 409

    def test_get_logs(self):
        r = self.client.get("/logs")
        assert r.status_code == 200
        data = r.get_json()
        assert "logs" in data and "count" in data

    def test_get_logs_filter_by_meal(self):
        self.client.post("/logs", json={"date": "2030-03-01", "meal_type": "Dinner",
                                        "actual_headcount": 300, "cooked_for": 350})
        self.client.post("/logs", json={"date": "2030-03-02", "meal_type": "Lunch",
                                        "actual_headcount": 250, "cooked_for": 290})
        r = self.client.get("/logs?meal=Dinner")
        data = r.get_json()
        assert data["count"] == 1
        assert data["logs"][0]["meal_type"] == "Dinner"

    def test_delete_log(self):
        self.client.post("/logs", json={"date": "2030-04-01", "meal_type": "Breakfast",
                                        "actual_headcount": 150, "cooked_for": 190})
        r = self.client.delete("/logs?date=2030-04-01&meal=Breakfast")
        assert r.status_code == 200

    def test_delete_nonexistent_log(self):
        assert self.client.delete("/logs?date=2099-12-31&meal=Dinner").status_code == 404

    # Analytics
    def test_waste_graph(self):
        self.client.post("/logs", json={"date": "2030-05-01", "meal_type": "Dinner",
                                        "actual_headcount": 300, "cooked_for": 360})
        r = self.client.get("/analytics/waste-graph")
        assert r.status_code == 200
        assert r.get_json()["data_points"] == 1

    def test_savings(self):
        r = self.client.get("/analytics/savings")
        assert r.status_code == 200
        assert "money_wasted_inr" in r.get_json()

    def test_predict_log_analytics_flow(self):
        prediction = self.client.get("/predict?date=2030-06-01&meal=Dinner")
        assert prediction.status_code == 200
        cooked_for = prediction.get_json()["predicted_headcount"]

        logged = self.client.post("/logs", json={
            "date": "2030-06-01",
            "meal_type": "Dinner",
            "actual_headcount": cooked_for - 12,
            "cooked_for": cooked_for,
        })
        assert logged.status_code == 201

        logs = self.client.get("/logs?meal=Dinner").get_json()
        assert logs["count"] == 1
        assert logs["logs"][0]["waste_headcount"] == 12

        savings = self.client.get("/analytics/savings").get_json()
        assert savings["total_sessions_logged"] == 1
        assert savings["money_wasted_inr"] == 12 * 60

    # Calendar
    def test_calendar_detect_festival(self):
        r = self.client.get("/calendar/detect?date=2025-10-21")
        assert r.status_code == 200
        assert r.get_json()["event_flag"] == "festival"

    def test_calendar_detect_missing_date(self):
        assert self.client.get("/calendar/detect").status_code == 400

    def test_calendar_upcoming(self):
        r = self.client.get("/calendar/upcoming?days=14")
        assert r.status_code == 200
        assert "events" in r.get_json()
