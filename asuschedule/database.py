from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import (
    USE_SQLITE_DATABASE,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_NAME,
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
