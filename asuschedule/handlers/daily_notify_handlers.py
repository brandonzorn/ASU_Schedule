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

from database import session
from models import User
from utils import require_registration

TIME_SELECTION = 1


@require_registration
async def keyboard_time(update: Update, _) -> int:
    keyboard = [
        [InlineKeyboardButton("8:00", callback_data="8")],
        [InlineKeyboardButton("20:00", callback_data="20")],
        [InlineKeyboardButton("Выключить", callback_data="disable")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Настройка ежедневной рассылки:",
        reply_markup=reply_markup,
    )
    return TIME_SELECTION


async def time_selection(update: Update, _):
    query = update.callback_query
    await query.answer()

    selected_time = query.data
    user = session.query(User).filter_by(id=query.from_user.id).first()
    if user:
        if selected_time == "disable":
            await query.edit_message_text(
                "Ежедневная рассылка выключена",
            )
            user.daily_notify = False
        else:
            user.notify_time = int(selected_time)
            user.daily_notify = True
            await query.edit_message_text(
                f"Вы выбрали время рассылки: {selected_time} часов",
            )
        session.commit()

    return ConversationHandler.END


async def cancel(update: Update, _):
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
