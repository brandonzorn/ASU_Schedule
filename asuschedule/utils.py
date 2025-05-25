from functools import wraps

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import INVERT_WEEK_PARITY
from database import session
from enums import UserRole, UserStatus
from models import User


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Расписание на сегодня", "Расписание на завтра"],
            ["Выбрать день", "Информация"],
            ["Ежедневная рассылка", "Изменить группу"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def require_registration(func):
    @wraps(func)
    async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs,
    ):
        user = session.get(User, update.effective_user.id)
        if user is None or (not user.role == UserRole.TEACHER and user.group_id is None):
            await update.message.reply_text(
                "Вы не зарегистрированы или не завершили настройку. "
                "Пожалуйста, начните с команды /start.",
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_staff(func):
    @wraps(func)
    async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs,
    ):
        user = session.get(User, update.effective_user.id)
        if user is None or not user.status == UserStatus.ADMIN:
            await update.message.reply_text(
                "⛔ У вас нет доступа к этой команде.",
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


def is_even_week(date) -> bool:
    week_number = date.isocalendar()[1]
    if INVERT_WEEK_PARITY:
        return not week_number % 2 == 0
    return week_number % 2 == 0


__all__ = [
    "get_main_keyboard",
    "is_even_week",
    "require_registration",
    "require_staff",
]
