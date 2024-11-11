import datetime
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN
from consts import LESSON_TIMES, TIMEZONE
from database import session
from handlers import schedules_table_handler, registration_handler
from models import User

from schedules.schedules_text import get_next_lesson_text, get_schedule_text
from schedules.schedules import get_schedule_by_lesson_num, get_schedules
from utils import check_user_registration, is_even_week

__all__ = []


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await check_user_registration(update, context)
    if user is None:
        return
    keyboard = [
        [
            InlineKeyboardButton(
                "Изменить группу",
                callback_data="change_group",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        user.to_text(),
        reply_markup=reply_markup,
    )


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await check_user_registration(update, context)
    if user is None:
        return

    date = datetime.date.today()
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    if not schedules:
        await update.message.reply_text("Расписание не найдено.")
        return
    schedule_text = get_schedule_text(schedules, date)
    await update.message.reply_text(schedule_text, parse_mode=ParseMode.HTML)


async def next_day_schedule_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = await check_user_registration(update, context)
    if user is None:
        return
    date = datetime.date.today() + datetime.timedelta(days=1)
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    if not schedules:
        await update.message.reply_text("Расписание не найдено.")
        return
    schedule_text = get_schedule_text(schedules, date)
    await update.message.reply_text(schedule_text, parse_mode=ParseMode.HTML)


async def set_daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await check_user_registration(update, context)
    if user is None:
        return
    if user.daily_notify:
        await update.message.reply_text(
            "Ежедневная рассылка выключена",
        )
    else:
        await update.message.reply_text(
            "Ежедневная рассылка включена",
        )
    user.daily_notify = not user.daily_notify
    session.commit()


async def next_lesson_handler(context: ContextTypes.DEFAULT_TYPE, lesson_num: int):
    users = session.query(User).filter_by(daily_notify=True).all()
    for user in users:
        schedule = get_schedule_by_lesson_num(user, lesson_num + 1)
        if not schedule:
            return
        schedule_text = get_next_lesson_text(schedule)
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode=ParseMode.HTML,
        )


async def daily_schedule_handler(
        context: ContextTypes.DEFAULT_TYPE, next_day=False,
) -> None:
    users = session.query(User).filter_by(daily_notify=True).all()
    date = (
        datetime.date.today() + datetime.timedelta(days=1)
        if next_day else datetime.date.today()
    )
    for user in users:
        schedules = get_schedules(user, date.weekday(), is_even_week(date))
        if not schedules:
            await context.bot.send_message(
                chat_id=user.id,
                text="Расписание не найдено.",
            )
            return
        schedule_text = get_schedule_text(schedules, date)
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode=ParseMode.HTML,
        )


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_daily(
        daily_schedule_handler, datetime.time(
            hour=8,
            tzinfo=TIMEZONE,
        ),
    )
    job_queue.run_daily(
        lambda *args: daily_schedule_handler(*args, next_day=True), datetime.time(
            hour=20,
            tzinfo=TIMEZONE,
        ),
    )
    for lesson_num, times in LESSON_TIMES.items():
        hour, minute = [int(i) for i in times[1].split(":")]
        job_queue.run_daily(
            lambda x, y=lesson_num: next_lesson_handler(x, lesson_num=y),
            datetime.time(
                hour=hour,
                minute=minute,
                tzinfo=TIMEZONE,
            ),
            name=f"next_lesson_handler_{lesson_num}",
        )

    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("schedule", schedule_handler))
    application.add_handler(CommandHandler("schedule_next", next_day_schedule_handler))
    application.add_handler(CommandHandler("daily", set_daily_handler))

    application.add_handler(registration_handler)
    application.add_handler(schedules_table_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
