import datetime
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)

from config import BOT_TOKEN
from consts import LESSON_TIMES, TIMEZONE
from database import session
from handlers import (
    notify_time_handler,
    delete_all_schedules_handler,
    handle_file,
    message_handler,
    registration_handler,
    schedule_table_handler,
    turn_off_daily_notify_handler,
    users_list_handler,
    users_stats_handler,
    error_handler,
)
from models import User

from schedules.schedules_text import get_next_lesson_text, get_schedule_text
from schedules.schedules import get_schedules
from utils import get_main_keyboard, is_even_week, require_registration

__all__ = []

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(
            datetime.datetime.now(tz=TIMEZONE).strftime("logs/%Y-%m-%d_%H-%M-%S.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@require_registration
async def info_handler(update: Update, _) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    await update.message.reply_text(
        user.to_text(),
    )


@require_registration
async def schedule_handler(update: Update, _) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()

    date = datetime.datetime.now(tz=TIMEZONE)
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    schedule_text = get_schedule_text(user, schedules, date)
    await update.message.reply_text(
        schedule_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


@require_registration
async def next_day_schedule_handler(update: Update, _) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()

    date = datetime.datetime.now(tz=TIMEZONE) + datetime.timedelta(days=1)
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    schedule_text = get_schedule_text(user, schedules, date)
    await update.message.reply_text(
        schedule_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


async def next_lesson_handler(context: ContextTypes.DEFAULT_TYPE):
    lesson_num = context.job.data["lesson_num"]
    date = datetime.datetime.now(tz=TIMEZONE)

    users = session.query(User).filter_by(daily_notify=True).all()
    for user in users:
        schedules = get_schedules(
            user, date.weekday(),
            is_even_week(date),
            lesson_number=lesson_num + 1,
        )
        if not schedules:
            continue
        schedule_text = get_next_lesson_text(user, schedules[0])
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode=ParseMode.HTML,
        )


async def daily_schedule_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    notify_time = context.job.data["notify_time"]

    users = session.query(User).filter_by(
        daily_notify=True, notify_time=notify_time,
    ).all()
    date = (
        datetime.datetime.now(tz=TIMEZONE) + datetime.timedelta(days=1)
        if notify_time == 20 else datetime.datetime.now(tz=TIMEZONE)
    )
    for user in users:
        schedules = get_schedules(user, date.weekday(), is_even_week(date))
        schedule_text = get_schedule_text(user, schedules, date)
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode=ParseMode.HTML,
        )


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_daily(
        daily_schedule_handler,
        datetime.time(
            hour=8,
            tzinfo=TIMEZONE,
        ),
        data={"notify_time": 8},
        name="daily_notify_8",
    )
    job_queue.run_daily(
        daily_schedule_handler,
        datetime.time(
            hour=20,
            tzinfo=TIMEZONE,
        ),
        data={"notify_time": 20},
        name="daily_notify_20",
    )
    for lesson_num, times in LESSON_TIMES.items():
        hour, minute = [int(i) for i in times[1].split(":")]
        job_queue.run_daily(
            next_lesson_handler,
            datetime.time(
                hour=hour,
                minute=minute,
                tzinfo=TIMEZONE,
            ),
            data={"lesson_num": lesson_num},
            name=f"next_lesson_handler_{lesson_num}",
        )

    application.add_handler(CommandHandler("info", info_handler))
    application.add_handler(CommandHandler("schedule", schedule_handler))
    application.add_handler(CommandHandler("schedule_next", next_day_schedule_handler))

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Информация$"),
            info_handler,
        ),
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Расписание на сегодня$"),
            schedule_handler,
        ),
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Расписание на завтра$"),
            next_day_schedule_handler,
        ),
    )

    # Staff commands
    application.add_handler(message_handler)
    application.add_handler(users_list_handler)
    application.add_handler(users_stats_handler)
    application.add_handler(turn_off_daily_notify_handler)
    application.add_handler(delete_all_schedules_handler)
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.add_handler(registration_handler)
    application.add_handler(schedule_table_handler)
    application.add_handler(notify_time_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
