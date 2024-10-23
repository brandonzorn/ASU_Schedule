import os
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USE_ALTERNATE_LESSON_TIMES = True if os.getenv("USE_ALTERNATE_LESSON_TIMES") == "True" else False
USE_SQLITE_DATABASE = True if os.getenv("USE_SQLITE_DATABASE") == "True" else False
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
