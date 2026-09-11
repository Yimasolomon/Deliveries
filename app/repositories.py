from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Driver,
    Delivery,
    DeliveryStatusHistory,
)


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def add(self, customer: Customer) -> Customer:
        self.db.add(customer)
        return customer

    def get_by_id(self, customer_id: int) -> Customer | None:
        statement = select(Customer).where(Customer.id == customer_id)
        return self.db.scalar(statement)

    def get_all(self) -> list[Customer]:
        statement = select(Customer).order_by(Customer.id)
        return list(self.db.scalars(statement).all())


class DriverRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, driver: Driver) -> Driver:
        self.db.add(driver)
        self.db.commit()
        self.db.refresh(driver)
        return driver

    def add(self, driver: Driver) -> Driver:
        self.db.add(driver)
        return driver

    def get_by_id(self, driver_id: int) -> Driver | None:
        statement = select(Driver).where(Driver.id == driver_id)
        return self.db.scalar(statement)

    def get_all(self) -> list[Driver]:
        statement = select(Driver).order_by(Driver.id)
        return list(self.db.scalars(statement).all())


class DeliveryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, delivery: Delivery) -> Delivery:
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def add(self, delivery: Delivery) -> Delivery:
        self.db.add(delivery)
        return delivery

    def get_by_id(self, delivery_id: int) -> Delivery | None:
        statement = select(Delivery).where(Delivery.id == delivery_id)
        return self.db.scalar(statement)

    def get_by_tracking_number(
        self,
        tracking_number: str,
    ) -> Delivery | None:
        statement = select(Delivery).where(
            Delivery.tracking_number == tracking_number
        )
        return self.db.scalar(statement)

    def get_all(self) -> list[Delivery]:
        statement = select(Delivery).order_by(Delivery.id)
        return list(self.db.scalars(statement).all())


class DeliveryStatusHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        history: DeliveryStatusHistory,
    ) -> DeliveryStatusHistory:
        self.db.add(history)
        return history

    def get_for_delivery(
        self,
        delivery_id: int,
    ) -> list[DeliveryStatusHistory]:
        statement = (
            select(DeliveryStatusHistory)
            .where(
                DeliveryStatusHistory.delivery_id == delivery_id
            )
            .order_by(DeliveryStatusHistory.created_at)
        )

        return list(self.db.scalars(statement).all())
