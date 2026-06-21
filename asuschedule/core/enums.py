from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"


class UserStatus(StrEnum):
    USER = "user"
    ADMIN = "admin"


__all__ = [
    "UserRole",
    "UserStatus",
]
