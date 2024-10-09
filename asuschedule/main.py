import datetime

import pytz

from calendar import day_name

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from config import BOT_TOKEN
from consts import LESSON_TIMES
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
        f"""
Username: {user.name}
Group: {user.group.get_name()}
Subgroup: {user.subgroup}
        """,
        reply_markup=reply_markup,
    )


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await check_user_registration(update, context)
    if user is None:
        return

    current_day_of_week = datetime.datetime.now().weekday()
    schedules = session.query(Schedule).filter_by(
        group_id=user.group.id,
        day_of_week=current_day_of_week,
    ).order_by(Schedule.lesson_number).all()

    if not schedules:
        await update.message.reply_text("Расписание не найдено.")
        return
    schedule_text = f"<b>Расписание на {day_name[current_day_of_week]}:</b>\n\n"
    for schedule in schedules:
        if schedule.subgroup is None or schedule.subgroup == user.subgroup:
            teacher_profile_url = "/"
            start_time, end_time = LESSON_TIMES.get(schedule.lesson_number, ("-", "-"))
            schedule_text += (
                f"\t{schedule.lesson_number} пара ({start_time} - {end_time})\n"
                f"\t├Предмет: {schedule.subject}\n"
                f"\t├Кабинет: {schedule.room}\n"
                f"\t├Преподаватель: "
                f"<a href='{teacher_profile_url}'>{schedule.teacher}</a>\n"
                f"------------\n"
            )
    await update.message.reply_text(schedule_text, parse_mode="HTML")


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


async def daily_schedule_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    users = session.query(User).filter_by(daily_notify=True).all()
    for user in users:
        current_day_of_week = datetime.datetime.now().isoweekday()
        schedules = session.query(Schedule).filter_by(
            group_id=user.group.id,
            day_of_week=current_day_of_week,
        ).all()

        if not schedules:
            await context.bot.send_message(
                chat_id=user.id,
                text="Расписание не найдено.",
            )
            return
        schedule_text = f"<b>Расписание на {day_name[current_day_of_week - 1]}:</b>\n\n"
        for schedule in schedules:
            if schedule.subgroup is None or schedule.subgroup == user.subgroup:
                teacher_profile_url = "/"
                start_time, end_time = LESSON_TIMES.get(
                    schedule.lesson_number, ("-", "-"),
                )
                schedule_text += (
                    f"\t{schedule.lesson_number} пара ({start_time} - {end_time})\n"
                    f"\t├Предмет: {schedule.subject}\n"
                    f"\t├Кабинет: {schedule.room}\n"
                    f"\t├Преподаватель: "
                    f"<a href='{teacher_profile_url}'>{schedule.teacher}</a>\n"
                    f"------------\n"
                )
        await context.bot.send_message(
            chat_id=user.id,
            text=schedule_text,
            parse_mode="HTML",
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
