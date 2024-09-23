import logging
from calendar import weekday
from datetime import datetime
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from asuschedule.config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


schedule = {
    0: [
        {
            "num": 1,
            "group": 0,
            "name": "Эмоциональный интеллект и критическое мышление инженера",
            "teacher": "Хачецуков З.М."
        },
        {
            "num": 2,
            "group": 0,
            "name": "Основы проектной деятельности",
            "teacher": "Атагян Д.А.",
            "teacher_tg": "atadav00"
        },
        {
            "num": 3,
            "group": 1,
            "name": "Иностр. Язык",
            "teacher": "Копылова Ю.В."
        },
        {
            "num": 3,
            "group": 2,
            "name": "Физика",
            "teacher": "Шамбин А.И."
        }
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    print(user.mention_html())
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sub_group = 2
    date = datetime.now()
    cur_weekday = weekday(date.year, date.month, date.day)
    text = ""
    for sub in schedule[cur_weekday]:
        if sub["group"] in [0, sub_group]:
            text += f"{sub["num"]} Пара: {sub["name"]} - <a href=''>{sub["teacher"]}</a>\n"
    await update.message.reply_text(text)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
