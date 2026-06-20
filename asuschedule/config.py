from environs import env

env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
USE_ALTERNATE_LESSON_TIMES = env.bool("USE_ALTERNATE_LESSON_TIMES")
INVERT_WEEK_PARITY = env.bool("INVERT_WEEK_PARITY")
DATABASE_NAME = env.str("DATABASE_NAME")
