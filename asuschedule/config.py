import os

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USE_ALTERNATE_LESSON_TIMES = True if os.getenv(
    "USE_ALTERNATE_LESSON_TIMES",
) == "True" else False
INVERT_WEEK_PARITY = True if os.getenv(
    "INVERT_WEEK_PARITY",
) == "True" else False

DATABASE_NAME = os.getenv("DATABASE_NAME")
