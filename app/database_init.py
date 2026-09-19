import os

from app.database import Base, engine
from app.models import (
    Customer,
    Driver,
    Delivery,
    DeliveryStatusHistory,
)


def init_db() -> None:
    """
    Initialize the database for development and testing.

    Production databases should be managed with Alembic migrations.
    """
    environment = os.getenv("APP_ENV", "development").lower()

    if environment == "production":
        return

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")