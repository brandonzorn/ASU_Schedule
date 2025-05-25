from sqlalchemy import or_, select

from database import session
from enums import UserRole
from models import Schedule, User


def get_schedules(
        user: User,
        weekday: int,
        even_week: bool,
        lesson_number: int = None,
) -> list[Schedule]:
    stmt = select(Schedule).filter_by(
        is_even_week=even_week,
        day_of_week=weekday,
    )
    if user.role == UserRole.TEACHER:
        stmt = stmt.where(
            Schedule.teacher.ilike(f"%{user.teacher_name}%"),
        )
    else:
        stmt = stmt.filter_by(group_id=user.group_id).where(
            or_(
                Schedule.subgroup.is_(None),
                Schedule.subgroup == user.subgroup,
            ),
        )
    if lesson_number is not None:
        stmt = stmt.filter_by(lesson_number=lesson_number)
    stmt = stmt.order_by(Schedule.lesson_number)
    return session.execute(stmt).scalars().all()


__all__ = [
    "get_schedules",
]
