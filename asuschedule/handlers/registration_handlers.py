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

(
    SELECT_FACULTY,
    SELECT_COURSE,
    SELECT_SPECIALITY,
    SELECT_SUBGROUP,
    SELECT_TEACHER,
) = range(5)


async def start_registration(update: Update, _) -> int:
    faculties = [
        faculty[:32] for (faculty,) in session.query(
            Group.faculty,
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{faculty}", callback_data=f"regFac_{faculty}",
            ),
        ] for faculty in faculties
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="reg_cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите факультет:", reply_markup=reply_markup)
    return SELECT_FACULTY


async def select_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["faculty"] = query.data.split("_")[-1]

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
                f"{course} курс", callback_data=f"regCourse_{course}",
            ) for course in courses
        ],
        [InlineKeyboardButton("Преподаватель", callback_data="reg_teacher")],
        [InlineKeyboardButton("Отмена", callback_data="reg_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите курс:", reply_markup=reply_markup)
    return SELECT_COURSE


async def select_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["course"] = query.data.split("_")[-1]

    specialities = [
        speciality for (speciality,) in session.query(
            Group.speciality,
        ).filter(
            Group.course == context.user_data["course"],
            Group.faculty.ilike(f"%{context.user_data['faculty']}%"),
        ).distinct().all()
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{speciality[:32]}", callback_data=f"regSpec_{speciality[:24]}",
            ),
        ] for speciality in specialities
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="reg_cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите специальность:", reply_markup=reply_markup)
    return SELECT_SPECIALITY


async def select_teacher(update: Update, _) -> int:
    query = update.callback_query
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
            InlineKeyboardButton(f"{teacher}", callback_data=f"regTeacher_{teacher}"),
        ] for teacher in teachers
    ]
    keyboard.append(
        [
            InlineKeyboardButton("Отмена", callback_data="reg_cancel"),
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите преподавателя:", reply_markup=reply_markup)
    return SELECT_TEACHER


async def select_speciality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["speciality"] = query.data.split("_")[-1]

    keyboard = [
        [
            InlineKeyboardButton("1 Подгруппа", callback_data="regSubgroup_1"),
            InlineKeyboardButton("2 Подгруппа", callback_data="regSubgroup_2"),
        ],
        [InlineKeyboardButton("Отмена", callback_data="reg_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Выберите подгруппу:",
        reply_markup=reply_markup,
    )
    return SELECT_SUBGROUP


async def select_subgroup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    username = query.from_user.username
    subgroup = int(query.data.split("_")[-1])

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
        )
        new_user.make_student(group.id, subgroup)
        session.add(new_user)
        await query.edit_message_text(
            f"Регистрация завершена! Привет, {name}.",
        )
    else:
        user.make_student(group.id, subgroup)
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


async def finalize_registration(
        update: Update,
        _,
) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    username = query.from_user.username
    teacher_name = query.data.split("_")[-1]

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
    allow_reentry=True,
    entry_points=[
        CommandHandler("start", start_registration),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Изменить группу$"), start_registration,
        ),
    ],
    states={
        SELECT_FACULTY: [
            CallbackQueryHandler(select_faculty, pattern=r"^regFac_"),
        ],
        SELECT_COURSE: [
            CallbackQueryHandler(select_course, pattern=r"^regCourse_"),
            CallbackQueryHandler(select_teacher, pattern=r"^reg_teacher$"),
        ],
        SELECT_SPECIALITY: [
            CallbackQueryHandler(select_speciality, pattern=r"^regSpec_"),
        ],
        SELECT_SUBGROUP: [
            CallbackQueryHandler(select_subgroup, pattern=r"^regSubgroup_"),
        ],
        SELECT_TEACHER: [
            CallbackQueryHandler(finalize_registration, pattern=r"^regTeacher_"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^reg_cancel$"),
    ],
)


__all__ = [
    "registration_handler",
]
