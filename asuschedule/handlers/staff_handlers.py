from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from database import session
from models import User
from utils import require_staff


@require_staff
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    if not user.is_staff():
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
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
async def users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = session.query(User).filter_by(id=update.effective_user.id).first()
    if not user.is_staff():
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
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


message_handler = CommandHandler("message", message)
users_list_handler = CommandHandler("users_list", users_list)
users_stats_handler = CommandHandler("user_stats", users_stats)

__all__ = [
    message_handler,
    users_list_handler,
    users_stats_handler,
]
