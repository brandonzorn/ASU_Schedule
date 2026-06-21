from telegram import Update

from core.utils import require_registration
from database.connection import session
from database.models import User


@require_registration
async def info_handler(update: Update, _) -> None:
    user = session.get(User, update.effective_user.id)
    await update.message.reply_text(user.to_text())
