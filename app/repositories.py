from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

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

    def get_by_phone(self, phone: str) -> Customer | None:
        statement = select(Customer).where(
            Customer.phone == phone
        )
        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> Customer | None:
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
        statement = select(Driver).where(
            Driver.id == driver_id
        )
        return self.db.scalar(statement)

    def get_by_phone(self, phone: str) -> Driver | None:
        statement = select(Driver).where(
            Driver.phone == phone
        )
        return self.db.scalar(statement)

    def get_by_vehicle_number(
        self,
        vehicle_number: str,
    ) -> Driver | None:
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

    def count_active_deliveries(
        self,
        driver_id: int,
        exclude_delivery_id: int | None = None,
    ) -> int:
        statement = select(Delivery).where(
            Delivery.driver_id == driver_id,
            Delivery.status.not_in(
                {"delivered", "failed", "cancelled"}
            ),
        )

        if exclude_delivery_id is not None:
            statement = statement.where(
                Delivery.id != exclude_delivery_id
            )

        return len(
            list(self.db.scalars(statement).all())
        )


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
        statement = (
            select(Delivery)
            .where(Delivery.id == delivery_id)
        )
        return self.db.scalar(statement)

    def get_by_tracking_number(
        self,
        tracking_number: str,
    ) -> Delivery | None:
        statement = (
            select(Delivery)
            .where(
                Delivery.tracking_number == tracking_number
            )
        )
        return self.db.scalar(statement)

    def get_all(self) -> list[Delivery]:
        statement = (
            select(Delivery)
            .order_by(Delivery.id)
        )
        return list(
            self.db.scalars(statement).all()
        )

    def get_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Delivery], int]:
        """
        Return one page of deliveries together with
        the total number of matching deliveries.
        """
        filters = []

        if search:
            search_term = f"%{search.strip()}%"

            filters.append(
                or_(
                    Delivery.tracking_number.ilike(
                        search_term
                    ),
                    Customer.name.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Delivery.pickup_address.ilike(
                        search_term
                    ),
                    Delivery.delivery_address.ilike(
                        search_term
                    ),
                )
            )

        if status:
            filters.append(
                Delivery.status == status
            )

        base_query = (
            select(Delivery)
            .join(
                Customer,
                Delivery.customer_id == Customer.id,
            )
            .where(*filters)
        )

        count_query = (
            select(func.count(Delivery.id))
            .select_from(Delivery)
            .join(
                Customer,
                Delivery.customer_id == Customer.id,
            )
            .where(*filters)
        )

        total = self.db.scalar(count_query) or 0

        statement = (
            base_query
            .options(
                joinedload(Delivery.customer),
                joinedload(Delivery.driver),
            )
            .order_by(Delivery.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        deliveries = list(
            self.db.scalars(statement).all()
        )

        return deliveries, total

    def search(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[Delivery]:
        deliveries, _ = self.get_paginated(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
        )

        return deliveries


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

        return list(
            self.db.scalars(statement).all()
        )


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_deliveries(self) -> int:
        statement = select(func.count(Delivery.id))
        return self.db.scalar(statement) or 0

    def count_deliveries_by_status(
        self,
        status: str,
    ) -> int:
        statement = (
            select(func.count(Delivery.id))
            .where(Delivery.status == status)
        )
        return self.db.scalar(statement) or 0

    def get_all_deliveries(self) -> list[Delivery]:
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
        statement = select(func.count(Customer.id))
        return self.db.scalar(statement) or 0

    def count_drivers(self) -> int:
        statement = select(func.count(Driver.id))
        return self.db.scalar(statement) or 0

    def count_drivers_by_status(
        self,
        status: str,
    ) -> int:
        statement = (
            select(func.count(Driver.id))
            .where(Driver.status == status)
        )
        return self.db.scalar(statement) or 0