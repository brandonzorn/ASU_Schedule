from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

from consts import LESSON_TIMES

Base = declarative_base()


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course = Column(Integer, nullable=False)
    faculty = Column(String, nullable=False)
    speciality = Column(String, nullable=False)

    def get_name(self):
        return f"{self.course}_{self.faculty}_{self.speciality}"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True)
    name = Column(String, nullable=False)
    subgroup = Column(Integer, nullable=True)  # Подгруппа (1 или 2)
    group_id = Column(Integer, ForeignKey("groups.id"))
    is_teacher = Column(Boolean, default=False, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=True)
    daily_notify = Column(Boolean, default=False, nullable=True)
    notify_time = Column(Integer, default=8, nullable=False)  # Время рассылки (8 или 20)
    teacher_name = Column(String, nullable=True)

    group = relationship("Group", back_populates="users")

    def is_staff(self) -> bool:
        return bool(self.is_teacher or self.is_admin)

    def _get_status_str(self):
        if self.is_teacher:
            return "Преподаватель"
        if self.is_admin:
            return "Персонал"
        return "Пользователь"

    def _get_group_name_str(self):
        return self.teacher_name if self.is_teacher else self.group.get_name()

    def to_text(self) -> str:
        return (
            f"Имя пользователя: {self.name}\n"
            f"Группа: {self._get_group_name_str()}\n"
            f"Подгруппа: {self.subgroup}\n"
            f"Ежедневная рассылка: {'Включена' if self.daily_notify else 'Выключена'}\n"
            f"Время рассылки: {self.notify_time}:00\n"
            f"Статус: {self._get_status_str()}"
        )


Group.users = relationship("User", order_by=User.id, back_populates="group")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    teacher = Column(String, nullable=True)
    room = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    subgroup = Column(Integer, nullable=True)
    lesson_type = Column(String, nullable=True)
    # 0: черная, 1: красная
    is_even_week = Column(Boolean, nullable=False)

    group = relationship("Group", back_populates="schedules")

    def to_text(self) -> str:
        start_time, end_time = LESSON_TIMES.get(self.lesson_number, ("-", "-"))
        return (
            f"{self.lesson_number} пара ({start_time} - {end_time})\n"
            f"├Предмет: {self.subject or 'не указано'}\n"
            f"├Формат: {self.lesson_type or 'не указано'}\n"
            f"├Кабинет: {self.room or 'не указано'}\n"
            f"├Преподаватель: {self.teacher or 'не указано'}\n"
        )


Group.schedules = relationship("Schedule", order_by=Schedule.id, back_populates="group")


__all__ = [
    Group,
    User,
    Schedule,
]
