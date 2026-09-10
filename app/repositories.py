from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Driver, Delivery


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
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

    def get_by_id(self, delivery_id: int) -> Delivery | None:
        statement = select(Delivery).where(Delivery.id == delivery_id)
        return self.db.scalar(statement)

    def get_all(self) -> list[Delivery]:
        statement = select(Delivery).order_by(Delivery.id)
        return list(self.db.scalars(statement).all())
