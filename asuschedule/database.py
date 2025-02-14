from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import (
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_USER,
    USE_SQLITE_DATABASE,
)
from models import Base


if not USE_SQLITE_DATABASE:
    DATABASE_URL = (
        f"postgresql://{DATABASE_USER}:"
        f"{DATABASE_PASSWORD}@{DATABASE_HOST}:"
        f"{DATABASE_PORT}/{DATABASE_NAME}"
    )
else:
    Path("sqlite").mkdir(exist_ok=True)
    DATABASE_URL = "sqlite:///sqlite/database.db"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
