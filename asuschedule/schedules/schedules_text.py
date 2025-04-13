from consts import DAY_NAMES, WEEK_NAMES
from models import Schedule, User
from utils import is_even_week


def get_next_lesson_text(user: User, schedule: Schedule) -> str:
    return f"<b>🔔 Следующая пара:</b>\n\n{schedule.to_text(user.is_teacher)}"


def get_schedule_text(user: User, schedules: list[Schedule], date) -> str:
    day_name = DAY_NAMES[date.weekday()]
    week_name = WEEK_NAMES[int(is_even_week(date))]

    schedule_text = f"<b>🗓️ Расписание на {day_name} ({week_name}):</b>\n\n"
    if not schedules:
        schedule_text += "🎉 Занятий нет."
    else:
        for schedule in schedules:
            schedule_text += f"{schedule.to_text(user.is_teacher)}━━━━━━━━━━━━━━━━━━\n"
    return schedule_text


def get_schedule_text_by_day(
        user: User,
        schedules: list[Schedule],
        day: int,
        even_week: bool,
) -> str:
    day_name = DAY_NAMES[day]
    week_name = WEEK_NAMES[int(even_week)]

    schedule_text = f"<b>🗓️ Расписание на {day_name} ({week_name}):</b>\n\n"
    for schedule in schedules:
        schedule_text += f"{schedule.to_text(user.is_teacher)}━━━━━━━━━━━━━━━━━━\n"
    return schedule_text


__all__ = [
    get_next_lesson_text,
    get_schedule_text,
    get_schedule_text_by_day,
]
