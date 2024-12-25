from consts import WEEK_NAMES, DAY_NAMES
from utils import is_even_week


def get_next_lesson_text(schedule) -> str:
    return f"<b>Следующая пара:</b>\n\n{schedule.to_text()}"


def get_schedule_text(schedules, date) -> str:
    schedule_text = (
        f"<b>Расписание на {DAY_NAMES[date.weekday()]} "
        f"({WEEK_NAMES[int(is_even_week(date))]}):</b>\n\n"
    )
    for schedule in schedules:
        schedule_text += f"{schedule.to_text()}━━━━━━━━━━━━━━━━━━\n"
    return schedule_text


def get_schedule_text_by_day(schedules, day: int, even_week) -> str:
    schedule_text = (
        f"<b>Расписание на {DAY_NAMES[day]} "
        f"({WEEK_NAMES[int(even_week)]}):</b>\n\n"
    )
    for schedule in schedules:
        schedule_text += f"{schedule.to_text()}━━━━━━━━━━━━━━━━━━\n"
    return schedule_text


__all__ = [
    get_next_lesson_text,
    get_schedule_text,
    get_schedule_text_by_day,
]
