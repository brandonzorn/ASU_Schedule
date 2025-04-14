from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from consts import DAY_NAMES, WEEK_NAMES
from database import session
from models import User
from schedules.schedules import get_schedules
from schedules.schedules_text import get_schedule_text_by_day
from utils import require_registration

SELECT_DAY = 6


@require_registration
async def start_schedule(update: Update, _) -> int | None:
    keyboard = [
        [
            InlineKeyboardButton(
                f"{DAY_NAMES[day]} ({WEEK_NAMES[0]})",
                callback_data=f"scheduleDay_{day}_0",
            ),
            InlineKeyboardButton(
                f"{DAY_NAMES[day]} ({WEEK_NAMES[1]})",
                callback_data=f"scheduleDay_{day}_1",
            ),
        ] for day in DAY_NAMES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите день недели:",
        reply_markup=reply_markup,
    )
    return SELECT_DAY


async def select_day(update: Update, _) -> int | None:
    query = update.callback_query
    await query.answer()
    user_choice = query.data.split("_")

    user = session.query(User).filter_by(id=update.effective_user.id).first()

    day, is_even_week = (int(user_choice[-2]), bool(int(user_choice[-1])))

    schedules = get_schedules(user, day, is_even_week)
    schedules_text = get_schedule_text_by_day(user, schedules, day, is_even_week)

    await query.edit_message_text(text=schedules_text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def cancel(_update, _context):
    return ConversationHandler.END


schedule_table_handler = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("schedule_days", start_schedule),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Выбрать день$"),
            start_schedule,
        ),
    ],
    states={
        SELECT_DAY: [CallbackQueryHandler(select_day, pattern="^scheduleDay_")],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
)

__all__ = [
    schedule_table_handler,
]
