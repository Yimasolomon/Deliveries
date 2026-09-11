from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    deliveries: Mapped[list["Delivery"]] = relationship(
        back_populates="customer",
    )


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    vehicle_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="available",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    deliveries: Mapped[list["Delivery"]] = relationship(
        back_populates="driver",
    )


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    tracking_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id"),
        nullable=True,
        index=True,
    )

    pickup_address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    delivery_address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="deliveries",
    )

    driver: Mapped["Driver | None"] = relationship(
        back_populates="deliveries",
    )

    status_history: Mapped[list["DeliveryStatusHistory"]] = relationship(
        back_populates="delivery",
        cascade="all, delete-orphan",
        order_by="DeliveryStatusHistory.created_at",
    )


class DeliveryStatusHistory(Base):
    __tablename__ = "delivery_status_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    delivery_id: Mapped[int] = mapped_column(
        ForeignKey("deliveries.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    delivery: Mapped["Delivery"] = relationship(
        back_populates="status_history",
    )