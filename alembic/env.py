from logging.config import fileConfig
import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from app.database import Base
from app import models


# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


config = context.config


# Configure Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic uses our application's SQLAlchemy metadata.
target_metadata = Base.metadata


def get_database_url() -> str:
    """Return the database URL used by the application."""

    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_URL_POSTGRES_URL")
    )

    if not database_url:
        database_url = f"sqlite:///{BASE_DIR / 'data' / 'deliveries.db'}"

    # Use psycopg v3 with PostgreSQL.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using an active database connection."""

    configuration = config.get_section(config.config_ini_section) or {}

    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()