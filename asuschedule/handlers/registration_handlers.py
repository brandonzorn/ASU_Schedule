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

from database import session
from models import Group, User
from utils import get_main_keyboard

COURSE, FACULTY, SPECIALITY, SUBGROUP = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    courses = [
        course for (course,) in session.query(
            Group.course,
        ).order_by(
            Group.course,
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{course} курс", callback_data=f"{course}",
            ) for course in courses
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите курс:", reply_markup=reply_markup)
    return COURSE


async def change_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    courses = [
        course for (course,) in session.query(
            Group.course,
        ).order_by(
            Group.course,
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{course} курс", callback_data=f"{course}",
            ) for course in courses
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите курс:", reply_markup=reply_markup)
    return COURSE


async def course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["course"] = query.data

    faculties = [faculty for (faculty,) in session.query(Group.faculty).distinct().all()]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{faculty}", callback_data=f"{faculty}",
            ) for faculty in faculties
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите факультет:", reply_markup=reply_markup)
    return FACULTY


async def faculty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["faculty"] = query.data

    specialities = [
        speciality for (speciality,) in session.query(
            Group.speciality,
        ).filter(
            Group.course == context.user_data["course"],
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{speciality}", callback_data=f"{speciality}",
            ) for speciality in specialities
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите специальность:", reply_markup=reply_markup)
    return SPECIALITY


async def speciality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["speciality"] = query.data

    keyboard = [
        [
            InlineKeyboardButton("1 Подгруппа", callback_data="1"),
            InlineKeyboardButton("2 Подгруппа", callback_data="2"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите подгруппу:", reply_markup=reply_markup)
    return SUBGROUP


async def subgroup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    username = query.from_user.username
    subgroup = int(query.data)

    course = context.user_data["course"]
    faculty = context.user_data["faculty"]
    speciality = context.user_data["speciality"]

    group = session.query(Group).filter_by(
        course=course,
        faculty=faculty,
        speciality=speciality,
    ).first()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        new_user = User(
            id=user_id,
            username=username,
            name=name,
            subgroup=subgroup,
            group_id=group.id,
        )
        session.add(new_user)
        await query.edit_message_text(
            f"Регистрация завершена! Привет, {name}.",
        )
    else:
        user.subgroup = subgroup
        user.group_id = group.id
        await query.edit_message_text(
            "Ваша группа изменена.",
        )
    await query.message.reply_text(
        "Выберите одну из опций:",
        reply_markup=get_main_keyboard(),
    )
    session.commit()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


registration_handler = ConversationHandler(
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
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
)


__all__ = [
    registration_handler,
]
