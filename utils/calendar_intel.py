"""
SmartCook — Calendar Intelligence
Detects exam seasons, festival dates, and weekends to set EventFlag.
Edit EXAM_PERIODS and FESTIVAL_DATES to match your academic calendar.
"""

from datetime import date
from models.data_models import EventFlag

# ── Configurable calendar ────────────────────────────────────────────────────

# Exam periods: list of (start_date, end_date) inclusive
EXAM_PERIODS: list[tuple[date, date]] = [
    (date(2025, 11, 10), date(2025, 11, 25)),  # Mid-semester exams
    (date(2025, 12, 1),  date(2025, 12, 15)),  # End-semester exams
    (date(2026, 4, 5),   date(2026, 4, 20)),   # Summer mid-sems
    (date(2026, 5, 10),  date(2026, 5, 25)),   # Summer end-sems
]

# Festival / holiday dates (exact dates)
FESTIVAL_DATES: set[date] = {
    date(2025, 10, 2),   # Gandhi Jayanti
    date(2025, 10, 12),  # Dussehra
    date(2025, 10, 20),  # Diwali Eve
    date(2025, 10, 21),  # Diwali
    date(2025, 10, 22),  # Diwali Day 2
    date(2025, 11, 5),   # Bhai Dooj
    date(2025, 11, 15),  # Guru Nanak Jayanti
    date(2025, 12, 25),  # Christmas
    date(2026, 1, 14),   # Makar Sankranti
    date(2026, 1, 26),   # Republic Day
    date(2026, 3, 14),   # Holi
    date(2026, 3, 31),   # Id-ul-Fitr
    date(2026, 4, 14),   # Dr. Ambedkar Jayanti / Baisakhi
}

# ── Priority: Festival > Exam > Weekend > None ────────────────────────────────

def detect_event(target_date: date) -> EventFlag:
    """Return the highest-priority EventFlag for a given date."""
    if target_date in FESTIVAL_DATES:
        return EventFlag.FESTIVAL

    for start, end in EXAM_PERIODS:
        if start <= target_date <= end:
            return EventFlag.EXAM

    if target_date.weekday() >= 5:   # Saturday=5, Sunday=6
        return EventFlag.WEEKEND

    return EventFlag.NONE


def is_exam_period(target_date: date) -> bool:
    return any(s <= target_date <= e for s, e in EXAM_PERIODS)


def is_festival(target_date: date) -> bool:
    return target_date in FESTIVAL_DATES


def upcoming_events(days: int = 7) -> list[dict]:
    """Return events (non-None flags) for the next N days."""
    from datetime import timedelta
    today = date.today()
    events = []
    for i in range(days):
        d = today + timedelta(days=i)
        flag = detect_event(d)
        if flag != EventFlag.NONE:
            events.append({"date": d.isoformat(), "event": flag.value})
    return events