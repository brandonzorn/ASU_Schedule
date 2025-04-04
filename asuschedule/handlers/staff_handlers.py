import html
import json
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import session
from models import Schedule, User
from utils import require_staff


logger = logging.getLogger(__name__)


@require_staff
async def users_list(update: Update, _):
    users = session.query(User).all()
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
    users = session.query(User).all()
    await update.message.reply_text(
        f"<b>Статистика пользователей:</b>\n\n"
        f"Всего пользователей: {len(users)}\n"
        f"Преподавателей: {len([i for i in users if i.is_teacher])}\n"
        f"Включена ежедневная рассылка: {len([i for i in users if i.daily_notify])}",
        parse_mode=ParseMode.HTML,
    )


@require_staff
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        msg = " ".join(context.args)
        users = session.query(User).all()
        for user in users:
            await context.bot.send_message(chat_id=user.id, text=msg)
        await update.message.reply_text("Сообщение отправлено.")
    else:
        await update.message.reply_text("Пожалуйста, укажите сообщение после команды.")


@require_staff
async def turn_off_daily_notify(update: Update, _):
    session.query(User).update({User.daily_notify: False})
    session.commit()
    await update.message.reply_text(
        "Ежедневные уведомления отключены для всех пользователей.",
    )


@require_staff
async def delete_all_schedules(update: Update, _):
    session.query(Schedule).delete()
    session.commit()
    await update.message.reply_text("Все расписания успешно удалены.")


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

    admin_user = session.query(User).filter_by(is_admin=True).first()

    await context.bot.send_message(
        chat_id=admin_user.id,
        text=err_message,
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
    message_handler,
    users_list_handler,
    users_stats_handler,
    turn_off_daily_notify_handler,
    error_handler,
]
