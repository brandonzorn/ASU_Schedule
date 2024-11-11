import datetime
import logging

from telegram import (
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from consts import LESSON_TIMES, TIMEZONE
from database import session
from handlers import schedules_table_handler, registration_handler
from models import User

from schedules.schedules_text import get_next_lesson_text, get_schedule_text
from schedules.schedules import get_schedule_by_lesson_num, get_schedules
from utils import is_even_week, require_registration, get_main_keyboard

__all__ = []


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@require_registration
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    await update.message.reply_text(
        user.to_text(),
    )


@require_registration
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    if not user.is_staff():
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    users = session.query(User).all()
    await update.message.reply_text(
        "\n------------\n".join([user.to_text() for user in users]),
    )


@require_registration
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    if not user.is_staff():
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    if context.args:
        msg = " ".join(context.args)
        users = session.query(User).all()
        for user in users:
            await context.bot.send_message(chat_id=user.id, text=msg)
        await update.message.reply_text("Сообщение отправлено.")
    else:
        await update.message.reply_text("Пожалуйста, укажите сообщение после команды.")


@require_registration
async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()

    date = datetime.date.today()
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    if not schedules:
        await update.message.reply_text(
            "Расписание не найдено.",
            reply_markup=get_main_keyboard(),
        )
        return
    schedule_text = get_schedule_text(schedules, date)
    await update.message.reply_text(
        schedule_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


@require_registration
async def next_day_schedule_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()

    date = datetime.date.today() + datetime.timedelta(days=1)
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    if not schedules:
        await update.message.reply_text(
            "Расписание не найдено.",
            reply_markup=get_main_keyboard(),
        )
        return
    schedule_text = get_schedule_text(schedules, date)
    await update.message.reply_text(
        schedule_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


@require_registration
async def set_daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = session.query(User).filter_by(id=update.effective_user.id).first()

    if user.daily_notify:
        await update.message.reply_text(
            "Ежедневная рассылка выключена",
            reply_markup=get_main_keyboard(),
        )
    else:
        await update.message.reply_text(
            "Ежедневная рассылка включена",
            reply_markup=get_main_keyboard(),
        )
    user.daily_notify = not user.daily_notify
    session.commit()


async def next_lesson_handler(context: ContextTypes.DEFAULT_TYPE, lesson_num: int):
    users = session.query(User).filter_by(daily_notify=True).all()
    for user in users:
        schedule = get_schedule_by_lesson_num(user, lesson_num + 1)
        if not schedule:
            logger.info(f"Schedule for user {user.id} & lesson {lesson_num} not found")
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


async def handle_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    command = {
        "Расписание на сегодня": schedule_handler,
        "Расписание на завтра": next_day_schedule_handler,
        "Ежедневная рассылка": set_daily_handler,
        "Информация": info,
    }.get(user_text)

    if command:
        await command(update, context)
    else:
        await update.message.reply_text("Неизвестная команда. Используйте кнопки.")


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
    application.add_handler(CommandHandler("message", message))
    application.add_handler(CommandHandler("schedule", schedule_handler))
    application.add_handler(CommandHandler("schedule_next", next_day_schedule_handler))
    application.add_handler(CommandHandler("daily", set_daily_handler))

    # Staff commands
    application.add_handler(CommandHandler("users_list", users_list))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"(?i)^Изменить группу$"),
            handle_keyboard,
        ),
    )

    application.add_handler(registration_handler)
    application.add_handler(schedules_table_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
