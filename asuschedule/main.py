import datetime
import logging
from pathlib import Path

from telegram.ext import (
    Application,
    CommandHandler,
    filters,
    MessageHandler,
)

from config import BOT_TOKEN
from core.constants import LESSON_TIMES, TIMEZONE
from handlers.common import info_handler
from handlers.conversations.daily_notify import notify_time_handler
from handlers.conversations.registration import registration_handler
from handlers.conversations.schedule_table import schedule_table_handler
from handlers.import_document import handle_file
from handlers.schedule import (
    daily_schedule_handler,
    next_day_schedule_handler,
    next_lesson_handler,
    schedule_handler,
)
from handlers.staff import (
    delete_all_schedules_handler,
    error_handler,
    message_handler,
    turn_off_daily_notify_handler,
    users_list_handler,
    users_stats_handler,
)

__all__ = []

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(
            datetime.datetime.now(tz=TIMEZONE).strftime(
                "logs/%Y-%m-%d_%H-%M-%S.log",
            ),
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_daily(
        daily_schedule_handler,
        datetime.time(
            hour=8,
            tzinfo=TIMEZONE,
        ),
        data={"notify_time": 8},
        name="daily_notify_8",
    )
    job_queue.run_daily(
        daily_schedule_handler,
        datetime.time(
            hour=20,
            tzinfo=TIMEZONE,
        ),
        data={"notify_time": 20},
        name="daily_notify_20",
    )
    for lesson_num, times in LESSON_TIMES.items():
        hour, minute = [int(i) for i in times[1].split(":")]
        job_queue.run_daily(
            next_lesson_handler,
            datetime.time(
                hour=hour,
                minute=minute,
                tzinfo=TIMEZONE,
            ),
            data={"lesson_num": lesson_num},
            name=f"next_lesson_handler_{lesson_num}",
        )

    application.add_handler(CommandHandler("info", info_handler))
    application.add_handler(CommandHandler("schedule", schedule_handler))
    application.add_handler(
        CommandHandler("schedule_next", next_day_schedule_handler),
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Информация$"),
            info_handler,
        ),
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Расписание на сегодня$"),
            schedule_handler,
        ),
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Расписание на завтра$"),
            next_day_schedule_handler,
        ),
    )

    # Staff commands
    application.add_handler(message_handler)
    application.add_handler(users_list_handler)
    application.add_handler(users_stats_handler)
    application.add_handler(turn_off_daily_notify_handler)
    application.add_handler(delete_all_schedules_handler)
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.add_handler(registration_handler)
    application.add_handler(schedule_table_handler)
    application.add_handler(notify_time_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
