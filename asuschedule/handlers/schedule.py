import datetime

from sqlalchemy import select
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core.constants import TIMEZONE
from core.utils import get_main_keyboard, is_even_week, require_registration
from database.connection import session
from database.models import User
from services.schedules import get_schedules
from services.schedules_text import get_next_lesson_text, get_schedule_text


async def daily_schedule_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    notify_time = context.job.data["notify_time"]

    users = (
        session.execute(
            select(User).filter_by(
                daily_notify=True,
                notify_time=notify_time,
            ),
        )
        .scalars()
        .all()
    )
    date = (
        datetime.datetime.now(tz=TIMEZONE) + datetime.timedelta(days=1)
        if notify_time == 20
        else datetime.datetime.now(tz=TIMEZONE)
    )
    for user in users:
        schedules = get_schedules(user, date.weekday(), is_even_week(date))
        schedule_text = get_schedule_text(user, schedules, date)
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode=ParseMode.HTML,
        )


@require_registration
async def schedule_handler(update: Update, _) -> None:
    user = session.get(User, update.effective_user.id)

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
    user = session.get(User, update.effective_user.id)

    date = datetime.datetime.now(tz=TIMEZONE) + datetime.timedelta(days=1)
    schedules = get_schedules(user, date.weekday(), is_even_week(date))

    schedule_text = get_schedule_text(user, schedules, date)
    await update.message.reply_text(
        schedule_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


async def next_lesson_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    lesson_num = context.job.data["lesson_num"]
    date = datetime.datetime.now(tz=TIMEZONE)

    users = (
        session.execute(
            select(User).filter_by(daily_notify=True),
        )
        .scalars()
        .all()
    )
    for user in users:
        schedules = get_schedules(
            user,
            date.weekday(),
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
