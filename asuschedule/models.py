from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course = Column(Integer, nullable=False)
    faculty = Column(String, nullable=False)
    speciality = Column(String, nullable=False)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    subgroup = Column(Integer, nullable=False)  # Подгруппа (1 или 2)
    group_id = Column(Integer, ForeignKey('groups.id'))

    group = relationship('Group', back_populates='users')


Group.users = relationship('User', order_by=User.id, back_populates='group')


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    teacher = Column(String, nullable=False)
    room = Column(String, nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'))
    subgroup = Column(Integer, nullable=True)

    group = relationship('Group', back_populates='schedules')


Group.schedules = relationship('Schedule', order_by=Schedule.id, back_populates='group')
