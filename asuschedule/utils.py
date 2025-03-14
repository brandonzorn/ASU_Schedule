from functools import wraps

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import INVERT_WEEK_PARITY
from database import session
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
        user = session.query(User).filter_by(id=update.effective_user.id).first()
        if user is None:
            await update.message.reply_text(
                "Вы не зарегистрированы. Пожалуйста, начните с команды /start.",
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_staff(func):
    @wraps(func)
    async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs,
    ):
        user = session.query(User).filter_by(id=update.effective_user.id).first()
        if user is None or not user.is_staff():
            await update.message.reply_text(
                "У вас нет доступа к этой команде.",
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
    require_registration,
    is_even_week,
]
