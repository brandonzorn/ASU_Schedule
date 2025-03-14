from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from database import session
from models import User

TIME_SELECTION = 1


async def keyboard_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("8:00", callback_data="8")],
        [InlineKeyboardButton("20:00", callback_data="20")],
        [InlineKeyboardButton("Включить/Выключить", callback_data="toggle")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Настройка ежедневной рассылки:",
        reply_markup=reply_markup,
    )
    return TIME_SELECTION


async def time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_time = query.data
    user_id = query.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        if selected_time == "toggle":
            if user.daily_notify:
                await query.edit_message_text(
                    "Ежедневная рассылка выключена",
                )
            else:
                await query.edit_message_text(
                    "Ежедневная рассылка включена",
                )
            user.daily_notify = not user.daily_notify
        else:
            user.notify_time = int(selected_time)
            await query.edit_message_text(
                f"Вы выбрали время рассылки: {selected_time} часов",
            )
        session.commit()

    return ConversationHandler.END


async def cancel(update, context):
    await update.message.reply_text("Настройка рассылки отменена.")
    return ConversationHandler.END


daily_time_selection_handler = ConversationHandler(
    entry_points=[
        CommandHandler("notify_time", keyboard_time),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Ежедневная рассылка$"),
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
