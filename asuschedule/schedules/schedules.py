from sqlalchemy import or_

from database import session
from enums import UserRole
from models import Schedule, User


def get_schedules(
        user: User,
        weekday: int,
        even_week: bool,
        lesson_number: int = None,
) -> list[Schedule]:
    query = session.query(Schedule).filter_by(
        is_even_week=even_week,
        day_of_week=weekday,
    )
    if user.role == UserRole.TEACHER:
        query = query.filter(
            Schedule.teacher.ilike(f"%{user.teacher_name}%"),
        )
    else:
        query = query.filter_by(group_id=user.group_id).filter(
            or_(
                Schedule.subgroup.is_(None),
                Schedule.subgroup == user.subgroup,
            ),
        )
    if lesson_number is not None:
        query = query.filter(Schedule.lesson_number == lesson_number)
    return query.order_by(Schedule.lesson_number).all()


__all__ = [
    "get_schedules",
]
