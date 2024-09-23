from calendar import day_name
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from asuschedule.config import BOT_TOKEN
from asuschedule.database import session
from asuschedule.models import Group, User, Schedule

COURSE, FACULTY, SPECIALITY, SUBGROUP = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    courses = [course for (course,) in session.query(Group.course).distinct().all()]
    keyboard = [
        [InlineKeyboardButton(f"{course} курс", callback_data=f"{course}") for course in courses],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите курс:", reply_markup=reply_markup)
    return COURSE


async def course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['course'] = query.data

    faculties = [faculty for (faculty,) in session.query(Group.faculty).distinct().all()]
    keyboard = [
        [InlineKeyboardButton(f"{faculty}", callback_data=f"{faculty}") for faculty in faculties],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите факультет:", reply_markup=reply_markup)
    return FACULTY


async def faculty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['faculty'] = query.data

    specialities = [speciality for (speciality,) in session.query(Group.speciality).distinct().all()]
    keyboard = [
        [InlineKeyboardButton(f"{speciality}", callback_data=f"{speciality}") for speciality in specialities],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите специальность:", reply_markup=reply_markup)
    return SPECIALITY


async def speciality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['speciality'] = query.data

    keyboard = [
        [InlineKeyboardButton("1 Подгруппа", callback_data="1"),
         InlineKeyboardButton("2 Подгруппа", callback_data="2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите подгруппу:", reply_markup=reply_markup)
    return SUBGROUP


async def subgroup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    subgroup = int(query.data)

    course = context.user_data['course']
    faculty = context.user_data['faculty']
    speciality = context.user_data['speciality']

    group = session.query(Group).filter_by(
        course=course,
        faculty=faculty,
        speciality=speciality,
    ).first()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        new_user = User(id=user_id, name=name, subgroup=subgroup, group_id=group.id)
        session.add(new_user)
        session.commit()
        await query.edit_message_text(f"Регистрация завершена! Привет, {name}.")
    else:
        await query.edit_message_text("Вы уже зарегистрированы.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        await update.message.reply_text("Вы не зарегистрированы.")
    await update.message.reply_text(
        f"""
Username: {user.name}
Group: {user.group.course}_{user.group.faculty}_{user.group.speciality}
Subgroup: {user.subgroup}
        """
    )


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        await update.message.reply_text("Вы не зарегистрированы. Пожалуйста, начните с команды /start.")
        return

    current_day_of_week = datetime.now().isoweekday()
    schedules = session.query(Schedule).filter_by(
        group_id=user.group_id,
        day_of_week=current_day_of_week,
    ).all()

    if not schedules:
        await update.message.reply_text("Расписание не найдено.")
        return

    schedule_text = f"Расписание на {day_name[current_day_of_week - 1]}:\n\n"
    for schedule in schedules:
        if schedule.subgroup is None or schedule.subgroup == user.subgroup:
            schedule_text += f"{schedule.class_number} Пара: {schedule.subject}, {schedule.room}, {schedule.teacher}\n"
    await update.message.reply_text(schedule_text)


def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COURSE: [CallbackQueryHandler(course_callback)],
            FACULTY: [CallbackQueryHandler(faculty_callback)],
            SPECIALITY: [CallbackQueryHandler(speciality_callback)],
            SUBGROUP: [CallbackQueryHandler(subgroup_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("schedule", schedule))

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
