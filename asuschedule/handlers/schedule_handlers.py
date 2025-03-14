from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from consts import DAY_NAMES, WEEK_NAMES
from database import session
from models import Schedule
from schedules.schedules import get_schedules
from schedules.schedules_text import get_schedule_text_by_day

from models import User
from utils import require_registration

SELECT_DAY, SHOW_SCHEDULE = range(2)


@require_registration
async def schedules_table(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    days = [
        day for (day,) in session.query(
            Schedule.day_of_week,
        ).order_by(
            Schedule.day_of_week,
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{DAY_NAMES[day]} ({WEEK_NAMES[0]})",
                callback_data=f"{day}_0",
            ),
            InlineKeyboardButton(
                f"{DAY_NAMES[day]} ({WEEK_NAMES[1]})",
                callback_data=f"{day}_1",
            ),
        ] for day in days
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите день недели:",
        reply_markup=reply_markup,
    )
    return SELECT_DAY


async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query
    await query.answer()

    user = session.query(User).filter_by(id=update.effective_user.id).first()

    context.user_data["selected_day"] = query.data
    day_data = query.data.split("_")
    day, is_even_week = (int(day_data[0]), bool(int(day_data[1])))

    schedules = get_schedules(user, day, is_even_week)
    if not schedules:
        await query.edit_message_text("Расписание не найдено.")
        return ConversationHandler.END

    schedules_text = get_schedule_text_by_day(user, schedules, day, is_even_week)

    await query.edit_message_text(text=schedules_text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


schedules_table_handler = ConversationHandler(
    entry_points=[
        CommandHandler("schedule_days", schedules_table),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Выбрать день$"),
            schedules_table,
        ),
    ],
    states={
        SELECT_DAY: [CallbackQueryHandler(select_day)],
    },
    fallbacks=[CommandHandler("schedule_days", schedules_table)],
)

__all__ = [
    schedules_table_handler,
]
