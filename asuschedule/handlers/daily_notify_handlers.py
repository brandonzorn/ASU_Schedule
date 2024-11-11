from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler, CommandHandler,
)

from database import session
from models import User

TIME_SELECTION = 1


async def keyboard_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("8:00", callback_data="8")],
        [InlineKeyboardButton("20:00", callback_data="20")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите время для рассылки:",
        reply_markup=reply_markup,
    )
    return TIME_SELECTION


async def time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_time = int(query.data)
    user_id = query.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.notify_time = selected_time
        session.commit()
    await query.edit_message_text(f"Вы выбрали время рассылки: {selected_time} часов")

    return ConversationHandler.END


async def cancel(update, context):
    await update.message.reply_text("Изменение времени рассылки отменено.")
    return ConversationHandler.END


daily_time_selection_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Изменить время рассылки$"),
            keyboard_time,
        ),
    ],
    states={
        TIME_SELECTION: [
            CallbackQueryHandler(time_selection),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

__all__ = [
    daily_time_selection_handler,
]
