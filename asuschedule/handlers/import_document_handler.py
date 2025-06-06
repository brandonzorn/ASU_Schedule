import logging
from io import BytesIO

import pandas as pd
from sqlalchemy import select, delete
from telegram import Update

from consts import WEEK_NAMES
from database import session
from models import Group, Schedule
from utils import require_staff

days_of_week = {
    "пн": 0,
    "вт": 1,
    "ср": 2,
    "чт": 3,
    "пт": 4,
    "сб": 5,
    "вс": 6,
}


logger = logging.getLogger(__name__)


@require_staff
async def handle_file(update: Update, _):
    document = update.message.document

    if not document.file_name.endswith(".xlsx"):
        await update.message.reply_text(
            "Пожалуйста, отправьте файл в формате Excel (.xlsx).",
        )
        return

    file = await document.get_file()
    file_data = await file.download_as_bytearray()
    file_io = BytesIO(file_data)

    await update.message.reply_text("Файл загружен. Обрабатываю данные...")
    try:
        dataframe = pd.read_excel(file_io, sheet_name=None)
        combined_df = pd.concat(
            dataframe.values(),
            ignore_index=True,
        ).replace({float("nan"): None})

        session.execute(delete(Schedule))

        for val in combined_df.values:
            course = val[0]
            speciality = val[1]
            subgroup = int(val[2]) if isinstance(val[2], (float, int)) else None
            day_of_week = str(val[3])
            lesson_number = int(val[4])
            subject = val[5]
            teacher = val[6] if isinstance(val[6], str) else None
            room = str(val[7]) if isinstance(val[7], (str, int)) else None
            lesson_type = val[8] if isinstance(val[8], str) else None
            is_even_week = bool(int(val[9]))
            faculty = val[10]

            num_day_of_week = days_of_week.get(day_of_week)

            group = session.execute(
                select(Group).filter_by(
                    course=course,
                    speciality=speciality,
                    faculty=faculty,
                ),
            ).scalar_one_or_none()
            if not group:
                group = Group(
                    course=course,
                    faculty=faculty,
                    speciality=speciality,
                )
                session.add(group)
                logger.info(
                    f"Добавлена новая группа {group.get_name()}",
                )

            session.add(
                Schedule(
                    day_of_week=num_day_of_week,
                    lesson_number=lesson_number,
                    subject=subject,
                    teacher=teacher,
                    room=room,
                    subgroup=subgroup,
                    group_id=group.id,
                    lesson_type=lesson_type,
                    is_even_week=is_even_week,
                ),
            )
            logger.info(
                f"Добавлено расписание для группы "
                f"{group.get_name()} и пары номер {lesson_number} "
                f"в {day_of_week} ({WEEK_NAMES[int(is_even_week)]}).",
            )

        session.commit()
        await update.message.reply_text(
            "Данные успешно загружены и сохранены в базу данных.",
        )
    except Exception as e:
        session.rollback()
        await update.message.reply_text(
            f"Произошла ошибка при обработке файла. {e}",
        )


__all__ = [
    "handle_file",
]
