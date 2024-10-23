from telegram import Update
from telegram.ext import ContextTypes

from database import session
from models import User


async def check_user_registration(
        update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> User | None:
    """Проверяет, зарегистрирован ли пользователь. Возвращает объект User или None."""
    user_id = update.effective_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        await update.message.reply_text(
            "Вы не зарегистрированы. Пожалуйста, начните с команды /start.",
        )
        return None
    return user


def is_even_week(date) -> bool:
    week_number = date.isocalendar()[1]
    return week_number % 2 == 0
