import datetime

import pytz

from calendar import day_name

from sqlalchemy import or_
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from config import BOT_TOKEN
from consts import LESSON_TIMES, WEEK_NAMES
from database import session
from handlers.registration_handlers import (
    course_callback,
    faculty_callback,
    speciality_callback,
    subgroup_callback,
    start,
    cancel,
    COURSE,
    FACULTY,
    SPECIALITY,
    SUBGROUP,
    change_group,
)
from models import User, Schedule


async def check_user_registration(
        update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> User | None:
    """Проверяет, зарегистрирован ли пользователь. Возвращает объект User или None."""
    user_id = update.effective_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        await update.message.reply_text(
            "Вы не зарегистрированы. Пожалуйста, начните с команды /start.",
        )
        return None
    return user


def is_even_week() -> bool:
    date = datetime.date.today()
    week_number = date.isocalendar()[1]
    return week_number % 2 == 0


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
    schedules = get_schedules(user)

    if not schedules:
        await update.message.reply_text("Расписание не найдено.")
        return
    schedule_text = get_schedule_text(schedules)
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


def get_schedules(user):
    current_day_of_week = datetime.datetime.now().weekday()
    return session.query(
        Schedule,
    ).filter_by(
        group_id=user.group.id,
        is_even_week=is_even_week(),
        day_of_week=current_day_of_week,
    ).filter(
        or_(
            Schedule.subgroup.is_(None),
            Schedule.subgroup == user.subgroup,
        ),
    ).order_by(
            Schedule.lesson_number,
    ).all()


def get_schedule_by_lesson_num(user, num):
    current_day_of_week = datetime.datetime.now().weekday()
    return session.query(
        Schedule,
    ).filter_by(
        group_id=user.group.id,
        day_of_week=current_day_of_week,
        is_even_week=is_even_week(),
        lesson_number=num,
    ).filter(
        or_(
            Schedule.subgroup.is_(None),
            Schedule.subgroup == user.subgroup,
        ),
    ).order_by(
        Schedule.lesson_number,
    ).first()


def get_schedule_text(schedules) -> str:
    current_day_of_week = datetime.datetime.now().weekday()
    schedule_text = (
        f"<b>Расписание на {day_name[current_day_of_week]} "
        f"({WEEK_NAMES[int(is_even_week())]}):</b>\n\n"
    )
    for schedule in schedules:
        schedule_text += f"{schedule.to_text()}------------\n"
    return schedule_text


def get_next_lesson_text(schedule) -> str:
    schedule_text = "<b>Следующая пара:</b>\n\n"
    schedule_text += f"{schedule.to_text()}------------\n"
    return schedule_text


async def next_lesson_handler(context: ContextTypes.DEFAULT_TYPE, lesson_num: int):
    # add filter
    users = session.query(User).all()
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


async def daily_schedule_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    users = session.query(User).filter_by(daily_notify=True).all()
    for user in users:
        schedules = get_schedules(user)
        if not schedules:
            await context.bot.send_message(
                chat_id=user.id,
                text="Расписание не найдено.",
            )
            return
        schedule_text = get_schedule_text(schedules)
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
            tzinfo=pytz.timezone("Europe/Moscow"),
        ),
    )
    for lesson_num, times in LESSON_TIMES.items():
        hour, minute = [int(i) for i in times[1].split(":")]
        job_queue.run_daily(
            lambda x, y=lesson_num: next_lesson_handler(x, lesson_num=y),
            datetime.time(
                hour=hour,
                minute=minute,
                tzinfo=pytz.timezone("Europe/Moscow"),
            ),
            name=f"next_lesson_handler_{lesson_num}",
        )
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(change_group, pattern="change_group"),
        ],
        states={
            COURSE: [CallbackQueryHandler(course_callback)],
            FACULTY: [CallbackQueryHandler(faculty_callback)],
            SPECIALITY: [CallbackQueryHandler(speciality_callback)],
            SUBGROUP: [CallbackQueryHandler(subgroup_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("schedule", schedule_handler))
    application.add_handler(CommandHandler("daily", set_daily_handler))

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
