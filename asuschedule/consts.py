from zoneinfo import ZoneInfo

from config import USE_ALTERNATE_LESSON_TIMES

LESSON_TIMES = {
    0: ("7:15", "8:50"),
    1: ("09:00", "10:35"),
    2: ("10:45", "12:20"),
    3: ("13:00", "14:35"),
    4: ("14:45", "16:20"),
    5: ("16:30", "18:05"),
} if not USE_ALTERNATE_LESSON_TIMES else {
    0: ("7:15", "8:50"),
    1: ("9:00", "9:45"),
    2: ("9:55", "10:40"),
    3: ("10:50", "11:35"),
    4: ("11:45", "12:30"),
}


WEEK_NAMES = {
    0: "черная",
    1: "красная",
}


DAY_NAMES = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


TIMEZONE = ZoneInfo("Europe/Moscow")
