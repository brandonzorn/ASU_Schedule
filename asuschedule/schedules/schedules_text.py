import datetime

from consts import DAY_NAMES, WEEK_NAMES
from models import Schedule, User
from utils import is_even_week


def _build_schedule_text(
    user: User,
    schedules: list[Schedule],
    day_name: str,
    week_name: str,
) -> str:
    schedule_text = f"<b>🗓️ Расписание на {day_name} ({week_name}):</b>\n\n"
    if not schedules:
        schedule_text += "🎉 Занятий нет."
    for schedule in schedules:
        schedule_text += f"{schedule.to_text(user.role)}━━━━━━━━━━━━━━━━━━\n"
    return schedule_text


def get_next_lesson_text(user: User, schedule: Schedule) -> str:
    return f"<b>🔔 Следующая пара:</b>\n\n{schedule.to_text(user.role)}"


def get_schedule_text(
    user: User,
    schedules: list[Schedule],
    date: datetime.datetime,
) -> str:
    day_name = DAY_NAMES[date.weekday()]
    week_name = WEEK_NAMES[int(is_even_week(date))]
    return _build_schedule_text(user, schedules, day_name, week_name)


def get_schedule_text_by_day(
    user: User,
    schedules: list[Schedule],
    day: int,
    even_week: bool,
) -> str:
    day_name = DAY_NAMES[day]
    week_name = WEEK_NAMES[int(even_week)]
    return _build_schedule_text(user, schedules, day_name, week_name)


__all__ = [
    "get_next_lesson_text",
    "get_schedule_text",
    "get_schedule_text_by_day",
]
