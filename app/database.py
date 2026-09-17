import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Use an external DATABASE_URL in production.
# Fall back to local SQLite during development.
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URL_POSTGRES_URL")
    or f"sqlite:///{DATA_DIR / 'deliveries.db'}"
)

# Use psycopg (v3) with PostgreSQL.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


class Base(DeclarativeBase):
    pass


# SQLite needs this option for local development.
# Other databases, such as PostgreSQL, do not need it.
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    # Only create the local data directory when SQLite is being used.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
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

