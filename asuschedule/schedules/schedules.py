import datetime

from sqlalchemy import or_

from database import session
from models import Schedule
from utils import is_even_week


def get_schedules(user, weekday: int, even_week: bool):
    return session.query(
        Schedule,
    ).filter_by(
        group_id=user.group.id,
        is_even_week=even_week,
        day_of_week=weekday,
    ).filter(
        or_(
            Schedule.subgroup.is_(None),
            Schedule.subgroup == user.subgroup,
        ),
    ).order_by(
            Schedule.lesson_number,
    ).all()


def get_schedule_by_lesson_num(user, num):
    date = datetime.date.today()
    return session.query(
        Schedule,
    ).filter_by(
        group_id=user.group.id,
        is_even_week=is_even_week(date),
        day_of_week=date.weekday(),
        lesson_number=num,
    ).filter(
        or_(
            Schedule.subgroup.is_(None),
            Schedule.subgroup == user.subgroup,
        ),
    ).order_by(
        Schedule.lesson_number,
    ).first()


def get_schedules_by_teacher(teacher_name: str):
    date = datetime.date.today()
    return session.query(
        Schedule,
    ).filter_by(
        is_even_week=is_even_week(date),
        day_of_week=date.weekday(),
    ).filter(
        Schedule.teacher.ilike(f"%{teacher_name}%"),
    ).order_by(
        Schedule.lesson_number,
    ).all()


__all__ = [
    get_schedules,
    get_schedule_by_lesson_num,
    get_schedules_by_teacher,
]
