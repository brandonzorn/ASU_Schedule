from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)

from consts import WEEK_NAMES, DAY_NAMES
from database import session
from models import Schedule

from utils import check_user_registration

SELECT_DAY, SHOW_SCHEDULE = range(2)


async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await schedules_table(update, context)


async def schedules_table(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    query = update.callback_query
    user = await check_user_registration(update, context)
    if user is None:
        return None
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


async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["selected_day"] = query.data

    day, is_even_week = query.data.split("_")
    # schedules =
    # schedules_text = get_schedule_text()

    await query.edit_message_text(text="text")
    return ConversationHandler.END


schedules_table_handler = ConversationHandler(
    entry_points=[CommandHandler("schedule_days", schedules_table)],
    states={
        SELECT_DAY: [CallbackQueryHandler(select_day)],
    },
    fallbacks=[CommandHandler("schedule_days", schedules_table)],
)
