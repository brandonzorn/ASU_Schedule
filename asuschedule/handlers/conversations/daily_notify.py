import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
)

from core.utils import require_registration
from database.connection import session
from database.models import User

logger = logging.getLogger(__name__)

SELECT_NOTIFY_TIME = 5


@require_registration
async def start_notify_time(update: Update, _) -> int:
    source_message = update.message
    if not source_message:
        logger.warning("Can't find message to reply to")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                "8:00 (Утром)",
                callback_data="notifyTime_8",
            ),
        ],
        [
            InlineKeyboardButton(
                "20:00 (Вечером)",
                callback_data="notifyTime_20",
            ),
        ],
        [
            InlineKeyboardButton(
                "Выключить",
                callback_data="notifyTime_disable",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await source_message.reply_text(
        "Выберите желаемое время для ежедневной рассылки расписания:",
        reply_markup=reply_markup,
    )
    return SELECT_NOTIFY_TIME


async def select_notify_time(update: Update, _) -> int:
    query = update.callback_query
    if query is None:
        logger.warning("Can't find callback query")
        return ConversationHandler.END

    await query.answer()
    user_choice = query.data.split(":")[-1]

    user = session.get(User, query.from_user.id)
    if not user:
        await query.edit_message_text("Пользователь не найден в базе данных.")
        return ConversationHandler.END
    if user_choice == "disable":
        await query.edit_message_text("Ежедневная рассылка выключена.")
        user.daily_notify = False
    else:
        user.notify_time = int(user_choice)
        user.daily_notify = True
        await query.edit_message_text(
            f"Вы выбрали время рассылки: {user_choice}:00",
        )
    session.commit()
    return ConversationHandler.END


async def cancel(update: Update, _) -> int:
    source_message = update.message
    if source_message is None:
        logger.warning("Can't find message")
        return ConversationHandler.END
    await source_message.reply_text("Настройка рассылки отменена.")
    return ConversationHandler.END


notify_time_handler = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("notify_time", start_notify_time),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Ежедневная рассылка$"),
            start_notify_time,
        ),
    ],
    states={
        SELECT_NOTIFY_TIME: [
            CallbackQueryHandler(select_notify_time, pattern="^notify_time:"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
)

__all__ = [
    "notify_time_handler",
]
