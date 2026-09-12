from datetime import datetime, UTC

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Delivery, DeliveryStatusHistory
from app.repositories import (
    CustomerRepository,
    DeliveryRepository,
    DeliveryStatusHistoryRepository,
    DriverRepository,
)


class DeliveryServiceError(Exception):
    """Base exception for delivery business-logic errors."""


class CustomerNotFoundError(DeliveryServiceError):
    pass


class DriverNotFoundError(DeliveryServiceError):
    pass


class DriverUnavailableError(DeliveryServiceError):
    pass


class DeliveryNotFoundError(DeliveryServiceError):
    pass


class InvalidDeliveryDataError(DeliveryServiceError):
    pass


class InvalidStatusError(DeliveryServiceError):
    pass


class DeliveryService:
    """
    Business logic for creating and managing deliveries.

    Database access is delegated to repositories.
    """

    INITIAL_STATUS = "pending"

    VALID_STATUSES = {
        "pending",
        "in_transit",
        "out_for_delivery",
        "delivered",
        "failed",
        "cancelled",
    }

    ALLOWED_TRANSITIONS = {
        "pending": {
            "in_transit",
            "failed",
            "cancelled",
        },
        "in_transit": {
            "out_for_delivery",
            "failed",
            "cancelled",
        },
        "out_for_delivery": {
            "delivered",
            "failed",
            "cancelled",
        },
        "delivered": set(),
        "failed": set(),
        "cancelled": set(),
    }

    def __init__(self, db: Session):
        self.db = db

        self.customers = CustomerRepository(db)
        self.drivers = DriverRepository(db)
        self.deliveries = DeliveryRepository(db)
        self.status_history = DeliveryStatusHistoryRepository(db)
        
    def create_delivery(
        self,
        *,
        customer_id: int,
        driver_id: int | None,
        pickup_address: str,
        delivery_address: str,
        scheduled_at: datetime | None = None,
    ) -> Delivery:
        """
        Create a delivery and its initial status-history record
        in one database transaction.
        """

        pickup_address = pickup_address.strip()
        delivery_address = delivery_address.strip()

        if not pickup_address:
            raise InvalidDeliveryDataError(
                "Pickup address is required."
            )

        if not delivery_address:
            raise InvalidDeliveryDataError(
                "Delivery address is required."
            )

        if customer_id <= 0:
            raise InvalidDeliveryDataError(
                "A valid customer is required."
            )

        if driver_id is not None and driver_id <= 0:
            raise InvalidDeliveryDataError(
                "Invalid driver."
            )

        customer = self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                f"Customer {customer_id} was not found."
            )

        driver = None

        if driver_id is not None:
            driver = self.drivers.get_by_id(driver_id)

            if driver is None:
                raise DriverNotFoundError(
                    f"Driver {driver_id} was not found."
                )

            if driver.status != "available":
                raise DriverUnavailableError(
                    f"Driver '{driver.name}' is not available."
                )

        delivery = Delivery(
            tracking_number="TEMP",
            customer_id=customer.id,
            driver_id=driver.id if driver else None,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            status=self.INITIAL_STATUS,
            scheduled_at=scheduled_at,
        )

        try:
            self.deliveries.add(delivery)
            self.db.flush()

            delivery.tracking_number = (
                f"DLV-{delivery.id:06d}"
            )

            history = DeliveryStatusHistory(
                delivery_id=delivery.id,
                status=self.INITIAL_STATUS,
                note="Delivery created.",
            )

            self.status_history.add(history)

            self.db.commit()
            self.db.refresh(delivery)

            return delivery

        except IntegrityError:
            self.db.rollback()

            raise DeliveryServiceError(
                "The delivery could not be created because "
                "of a database constraint."
            )

        except Exception:
            self.db.rollback()
            raise

    def get_delivery(
        self,
        delivery_id: int,
    ) -> Delivery:
        delivery = self.deliveries.get_by_id(delivery_id)

        if delivery is None:
            raise DeliveryNotFoundError(
                f"Delivery {delivery_id} was not found."
            )

        return delivery

    def get_status_history(
        self,
        delivery_id: int,
    ) -> list[DeliveryStatusHistory]:
        self.get_delivery(delivery_id)

        return self.status_history.get_for_delivery(
            delivery_id
        )

    def update_status(
        self,
        *,
        delivery_id: int,
        new_status: str,
        note: str | None = None,
    ) -> Delivery:
        """
        Update delivery status and create a status-history record
        in one database transaction.
        """

        new_status = new_status.strip().lower()

        if new_status not in self.VALID_STATUSES:
            raise InvalidStatusError(
                f"Invalid delivery status: {new_status}"
            )

        delivery = self.get_delivery(delivery_id)

        current_status = delivery.status

        if current_status == new_status:
            raise InvalidStatusError(
                f"Delivery is already '{new_status}'."
            )

        allowed_statuses = self.ALLOWED_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise InvalidStatusError(
                f"Cannot change delivery status from "
                f"'{current_status}' to '{new_status}'."
            )

        delivery.status = new_status

        if new_status == "delivered":
            delivery.delivered_at = datetime.now(UTC)
        elif current_status == "delivered":
            delivery.delivered_at = None

        history = DeliveryStatusHistory(
            delivery_id=delivery.id,
            status=new_status,
            note=note.strip() if note else None,
        )

        try:
            self.status_history.add(history)

            self.db.commit()
            self.db.refresh(delivery)

            return delivery

        except IntegrityError:
            self.db.rollback()

            raise DeliveryServiceError(
                "The delivery status could not be updated "
                "because of a database constraint."
            )

        except Exception:
            self.db.rollback()
            raise