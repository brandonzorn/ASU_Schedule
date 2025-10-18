import html
import json
import logging
import traceback

from sqlalchemy import delete, select
from sqlalchemy import update as sql_update
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import session
from enums import UserRole, UserStatus
from models import Schedule, User
from utils import require_staff

logger = logging.getLogger(__name__)


@require_staff
async def users_list(update: Update, _):
    users = session.execute(
        select(User).order_by(User.role),
    ).scalars().all()
    chunk_size = 15
    user_chunks = [users[i:i + chunk_size] for i in range(0, len(users), chunk_size)]

    for chunk in user_chunks:
        await update.message.reply_text(
            "\n------------\n".join(
                [user.to_text() for user in chunk],
            ),
        )


@require_staff
async def users_stats(update: Update, _):
    users = session.execute(select(User)).scalars().all()
    await update.message.reply_text(
        f"📊 <b>Статистика пользователей:</b>\n\n"
        f"▪️ Всего пользователей: {len(users)}\n"
        f"▪️ Преподавателей: {len([i for i in users if i.role == UserRole.TEACHER])}\n"
        f"▪️ Включена ежедневная рассылка: {len([i for i in users if i.daily_notify])}",
        parse_mode=ParseMode.HTML,
    )


@require_staff
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        msg = " ".join(context.args)
        users = session.execute(select(User)).scalars().all()
        for user in users:
            await context.bot.send_message(chat_id=user.id, text=msg)
        await update.message.reply_text("✅ Сообщение отправлено.")
    else:
        await update.message.reply_text(
            "⚠️ Пожалуйста, укажите сообщение после команды.",
        )


@require_staff
async def turn_off_daily_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "confirm" not in context.args:
        await update.message.reply_text(
            "❗ Требуется подтверждение операции (укажите 'confirm' после команды).",
        )
        return
    session.execute(
        sql_update(User).values(daily_notify=False),
    )
    session.commit()
    await update.message.reply_text(
        "🌙 Ежедневные уведомления отключены для всех пользователей.",
    )


@require_staff
async def delete_all_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "confirm" not in context.args:
        await update.message.reply_text(
            "❗ Требуется подтверждение операции (укажите 'confirm' после команды).",
        )
        return
    session.execute(delete(Schedule))
    session.commit()
    await update.message.reply_text(
        "🗑️ Все расписания успешно удалены.",
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(
        "Exception while handling an update:",
        exc_info=context.error,
    )
    tb_list = traceback.format_exception(
        None,
        context.error,
        context.error.__traceback__,
    )
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    err_message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(
            json.dumps(update_str, indent=2, ensure_ascii=False),
        )}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    admin_user = session.execute(
        select(User).filter_by(status=UserStatus.ADMIN),
    ).scalar_one_or_none()
    if admin_user:
        await context.bot.send_message(
            chat_id=admin_user.id,
            text=err_message,
            parse_mode=ParseMode.HTML,
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="😔 Ой, что-то пошло не так... Произошла внутренняя ошибка.",
        parse_mode=ParseMode.HTML,
    )


message_handler = CommandHandler("message", message)
users_list_handler = CommandHandler("users_list", users_list)
users_stats_handler = CommandHandler("users_stats", users_stats)
turn_off_daily_notify_handler = CommandHandler(
    "turn_off_daily_notify",
    turn_off_daily_notify,
)
delete_all_schedules_handler = CommandHandler(
    "delete_all_schedules",
    delete_all_schedules,
)

__all__ = [
    "delete_all_schedules_handler",
    "error_handler",
    "message_handler",
    "turn_off_daily_notify_handler",
    "users_list_handler",
    "users_stats_handler",
]
