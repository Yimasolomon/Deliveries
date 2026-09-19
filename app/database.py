import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").lower()

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URL_POSTGRES_URL")
)

# Production must use an external database.
if APP_ENV == "production" and not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL must be set in production."
    )

# Use local SQLite during development when no database is configured.
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'deliveries.db'}"

# Use psycopg (v3) with PostgreSQL.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


class Base(DeclarativeBase):
    pass


connect_args = {}
engine_options = {}

if DATABASE_URL.startswith("sqlite"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connect_args = {
        "check_same_thread": False,
    }

else:
    # Keep stale database connections from being reused.
    engine_options = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_options,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()