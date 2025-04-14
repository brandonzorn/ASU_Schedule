from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Message,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from database import session
from models import Group, Schedule, User
from utils import get_main_keyboard

FACULTY, COURSE, SPECIALITY, SUBGROUP, TEACHER = range(5)


async def start(update: Update, _) -> int:
    faculties = [
        faculty[:32] for (faculty,) in session.query(
            Group.faculty,
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{faculty}", callback_data=f"{faculty}",
            ),
        ] for faculty in faculties
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите факультет:", reply_markup=reply_markup)
    return FACULTY


async def faculty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()
    context.user_data["faculty"] = query.data
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
        [InlineKeyboardButton("Преподаватель", callback_data="teacher")],
        [InlineKeyboardButton("Отмена", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите курс:", reply_markup=reply_markup)
    return COURSE


async def course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()
    context.user_data["course"] = query.data

    specialities = [
        speciality[:32] for (speciality,) in session.query(
            Group.speciality,
        ).filter(
            Group.course == context.user_data["course"],
            Group.faculty.ilike(f"%{context.user_data['faculty']}%"),
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{speciality}", callback_data=f"{speciality}",
            ) for speciality in specialities
        ],
        [InlineKeyboardButton("Отмена", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите специальность:", reply_markup=reply_markup)
    return SPECIALITY


async def speciality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()
    context.user_data["speciality"] = query.data

    keyboard = [
        [
            InlineKeyboardButton("1 Подгруппа", callback_data="1"),
            InlineKeyboardButton("2 Подгруппа", callback_data="2"),
        ],
        [InlineKeyboardButton("Отмена", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Выберите подгруппу:",
        reply_markup=reply_markup,
    )
    return SUBGROUP


async def subgroup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    username = query.from_user.username
    subgroup = int(query.data)

    course = context.user_data["course"]
    faculty = context.user_data["faculty"]
    speciality = context.user_data["speciality"]

    group = session.query(Group).filter(
        Group.course == course,
        Group.faculty.ilike(f"%{faculty}%"),
        Group.speciality.ilike(f"%{speciality}%"),
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
        user.remove_teacher_status()
        await query.edit_message_text(
            "Ваша группа изменена.",
        )
    if isinstance(query.message, Message):
        await query.message.reply_text(
            "Теперь вам доступны команды бота!",
            reply_markup=get_main_keyboard(),
        )
    session.commit()
    return ConversationHandler.END


async def teacher_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()

    teachers = [
        teacher for (teacher,) in session.query(
            Schedule.teacher,
        ).filter(
            Schedule.teacher.isnot(None),
            ~Schedule.teacher.contains("/"),
        ).distinct().order_by(Schedule.teacher).all()
    ]

    keyboard = [
        [
            InlineKeyboardButton(f"{teacher}", callback_data=f"{teacher}"),
        ] for teacher in teachers
    ]
    keyboard.append(
        [
            InlineKeyboardButton("Отмена", callback_data="cancel"),
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите преподавателя:", reply_markup=reply_markup)
    return TEACHER


async def finalize_registration(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if query.data == "cancel":
        return await cancel(update, context)
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    username = query.from_user.username
    teacher_name = query.data

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        new_user = User(
            id=user_id,
            username=username,
            name=name,
        )
        new_user.make_teacher(teacher_name)
        session.add(new_user)
        await query.edit_message_text(
            f"Регистрация завершена! Преподаватель: {teacher_name}.",
        )
    else:
        user.make_teacher(teacher_name)
        await query.edit_message_text(
            f"Ваша информация обновлена. Преподаватель: {teacher_name}.",
        )
    if isinstance(query.message, Message):
        await query.message.reply_text(
            "Теперь вам доступны команды бота!",
            reply_markup=get_main_keyboard(),
        )
    session.commit()
    return ConversationHandler.END


async def cancel(update: Update, _) -> int:
    if update.message:
        await update.message.reply_text("Регистрация отменена.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Регистрация отменена.")
        await update.callback_query.answer()

    return ConversationHandler.END


registration_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & filters.Regex(r"(?i)^Изменить группу$"), start),
    ],
    states={
        FACULTY: [CallbackQueryHandler(faculty_callback)],
        COURSE: [
            CallbackQueryHandler(course_callback, pattern=r"^\d+$"),
            CallbackQueryHandler(teacher_callback, pattern="^teacher$"),
        ],
        SPECIALITY: [CallbackQueryHandler(speciality_callback)],
        SUBGROUP: [CallbackQueryHandler(subgroup_callback)],
        TEACHER: [CallbackQueryHandler(finalize_registration)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & filters.Regex(r"(?i)^Изменить группу$"), start),
    ],
)


__all__ = [
    registration_handler,
]
