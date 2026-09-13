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
        statement = select(Customer).where(
            Customer.id == customer_id
        )
        return self.db.scalar(statement)

    def get_by_phone(
        self,
        phone: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.phone == phone
        )
        return self.db.scalar(statement)

    def get_by_email(
        self,
        email: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.email == email
        )
        return self.db.scalar(statement)

    def get_all(self) -> list[Customer]:
        statement = select(Customer).order_by(Customer.name)
        return list(self.db.scalars(statement).all())

    def get_deliveries(self, customer_id: int) -> list[Delivery]:
        statement = (
            select(Delivery)
            .where(Delivery.customer_id == customer_id)
            .order_by(Delivery.created_at.desc())
        )
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

    def get_by_phone(self, phone: str) -> Driver | None:
        statement = select(Driver).where(Driver.phone == phone)
        return self.db.scalar(statement)

    def get_by_vehicle_number(self, vehicle_number: str) -> Driver | None:
        statement = select(Driver).where(
            Driver.vehicle_number == vehicle_number
        )
        return self.db.scalar(statement)

    def get_all(self) -> list[Driver]:
        statement = select(Driver).order_by(Driver.name)
        return list(self.db.scalars(statement).all())

    def get_deliveries(self, driver_id: int) -> list[Delivery]:
        statement = (
            select(Delivery)
            .where(Delivery.driver_id == driver_id)
            .order_by(Delivery.created_at.desc())
        )
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

class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_deliveries(self) -> int:
        from sqlalchemy import func

        statement = select(func.count(Delivery.id))
        return self.db.scalar(statement) or 0

    def count_deliveries_by_status(self, status: str) -> int:
        from sqlalchemy import func

        statement = (
            select(func.count(Delivery.id))
            .where(Delivery.status == status)
        )
        return self.db.scalar(statement) or 0

    def get_all_deliveries(self) -> list[Delivery]:
        from sqlalchemy.orm import joinedload

        statement = (
            select(Delivery)
            .options(
                joinedload(Delivery.customer),
                joinedload(Delivery.driver),
            )
            .order_by(Delivery.created_at.desc())
        )

        return list(
            self.db.scalars(statement).unique().all()
        )

    def get_recent_deliveries(
        self,
        limit: int = 10,
    ) -> list[Delivery]:
        from sqlalchemy.orm import joinedload

        statement = (
            select(Delivery)
            .options(
                joinedload(Delivery.customer),
                joinedload(Delivery.driver),
            )
            .order_by(Delivery.created_at.desc())
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).unique().all()
        )

    def count_customers(self) -> int:
        from sqlalchemy import func

        statement = select(func.count(Customer.id))
        return self.db.scalar(statement) or 0

    def count_drivers(self) -> int:
        from sqlalchemy import func

        statement = select(func.count(Driver.id))
        return self.db.scalar(statement) or 0

    def count_drivers_by_status(self, status: str) -> int:
        from sqlalchemy import func

        statement = (
            select(func.count(Driver.id))
            .where(Driver.status == status)
        )
        return self.db.scalar(statement) or 0
