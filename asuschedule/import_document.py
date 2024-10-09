import pandas as pd

from database import session
from models import Schedule, Group

dataframe1 = pd.read_excel("document.xlsx", sheet_name=None)

combined_df = pd.concat(
    dataframe1.values(), ignore_index=True,
).replace({float("nan"): None})

days_of_week = {
        "пн": 0,
        "вт": 1,
        "ср": 2,
        "чт": 3,
        "пт": 4,
        "сб": 5,
        "вс": 6,
    }

for val in combined_df.values:
    course = val[0]
    speciality = val[1]
    subgroup = int(val[2]) if isinstance(val[2], (float, int)) else None
    day_of_week = str(val[3])
    lesson_number = int(val[4])
    subject = val[5]
    teacher = val[6] if isinstance(val[6], str) else None
    room = str(val[7]) if isinstance(val[7], (str, int)) else None
    num_day_of_week = days_of_week.get(day_of_week)

    group = session.query(Group).filter_by(course=course, speciality=speciality).first()
    if not group:
        group = Group(
            course=course,
            faculty="ИНЖЕНЕРНО-ФИЗИЧЕСКИЙ",
            speciality=speciality,
        )
        session.add(group)

    existing_schedule = session.query(Schedule).filter_by(
        group_id=group.id,
        lesson_number=lesson_number,
        day_of_week=num_day_of_week,
        subgroup=subgroup,
    ).first()

    if existing_schedule:
        existing_schedule.day_of_week = num_day_of_week
        existing_schedule.subject = subject
        existing_schedule.teacher = teacher
        existing_schedule.room = room
        existing_schedule.subgroup = subgroup
        print(
            f"Обновлено расписание для группы "
            f"ID {group.get_name()} и пары номер {lesson_number} в {num_day_of_week}.",
        )
    else:
        session.add(
            Schedule(
                day_of_week=num_day_of_week,
                lesson_number=lesson_number,
                subject=subject,
                teacher=teacher,
                room=room,
                subgroup=subgroup,
                group_id=group.id,
            ),
        )
        print(
            f"Добавлено новое расписание для группы "
            f"ID {group.get_name()} и пары номер {lesson_number} в {num_day_of_week}.",
        )


session.commit()
