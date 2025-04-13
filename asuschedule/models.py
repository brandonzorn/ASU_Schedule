from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

from consts import LESSON_TIMES

Base = declarative_base()


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course = Column(Integer, nullable=False)
    faculty = Column(String, nullable=False)
    speciality = Column(String, nullable=False)

    def get_name(self) -> str:
        return f"{self.course}_{self.faculty}_{self.speciality}"

    def get_short_name(self) -> str:
        return f"{self.course}_{self.speciality}"


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
        return bool(self.is_admin)

    def make_teacher(self, teacher_name: str) -> None:
        self.is_teacher = True
        self.teacher_name = teacher_name

    def remove_teacher_status(self) -> None:
        self.is_teacher = False
        self.teacher_name = None

    def _get_status_str(self) -> str:
        if self.is_admin:
            return "Администратор"
        if self.is_teacher:
            return "Преподаватель"
        return "Пользователь"

    def to_text(self) -> str:
        status = self._get_status_str()
        notify_status = "Включена" if self.daily_notify else "Выключена"
        notify_time_str = f"{self.notify_time}:00" if self.daily_notify else "-"

        if self.is_teacher:
            return (
                f"👤 Имя пользователя: {self.name}\n"
                f"🧑‍🏫 Преподаватель: {self.teacher_name or 'Не указано'}\n"
                f"📧 Ежедневная рассылка: {notify_status}\n"
                f"⏰ Время рассылки: {notify_time_str}\n"
                f"👑 Статус: {status}"
            )
        if self.group:
            return (
                f"👤 Имя пользователя: {self.name}\n"
                f"🏛️ Факультет: {self.group.faculty}\n"
                f"🎓 Группа: {self.group.get_short_name()}\n"
                f"🔢 Подгруппа: {self.subgroup or 'Не указана'}\n"
                f"📧 Ежедневная рассылка: {notify_status}\n"
                f"⏰ Время рассылки: {notify_time_str}\n"
                f"👑 Статус: {status}"
            )
        return (
            f"👤 Имя пользователя: {self.name}\n"
            f"⚠️ Группа не выбрана. Завершите регистрацию (/start)."
        )


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

    def to_text(self, is_requesting_teacher: bool = False) -> str:
        start_time, end_time = LESSON_TIMES.get(self.lesson_number, ("-", "-"))
        details = [
            f"Предмет: {self.subject or 'не указано'}",
            f"Формат: {self.lesson_type or 'не указано'}",
            f"Кабинет: {self.room or 'не указано'}",
        ]
        if is_requesting_teacher:
            details.append(
                f"Группа: {self.group.get_short_name() if self.group else '??'}",
            )
        else:
            details.append(
                f"Преподаватель: {self.teacher or 'не указано'}",
            )

        return (
            f"🕒 {self.lesson_number} пара ({start_time} - {end_time})\n"
            f"├{'\n├'.join(details)}\n"
        )


Group.users = relationship("User", order_by=User.id, back_populates="group")
Group.schedules = relationship("Schedule", order_by=Schedule.id, back_populates="group")


__all__ = [
    Group,
    User,
    Schedule,
]
