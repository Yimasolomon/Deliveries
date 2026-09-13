from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Delivery, Driver
from app.repositories import DriverRepository


class DriverServiceError(Exception):
    """Base exception for driver service errors."""


class DriverNotFoundError(DriverServiceError):
    """Raised when a driver cannot be found."""


class DuplicateDriverError(DriverServiceError):
    """Raised when a driver already exists."""


class InvalidDriverDataError(DriverServiceError):
    """Raised when driver data is invalid."""


class InvalidDriverStatusError(DriverServiceError):
    """Raised when a driver status is invalid."""


class DriverService:
    VALID_STATUSES = {
        "available",
        "unavailable",
        "busy",
    }

    def __init__(self, db: Session):
        self.db = db
        self.drivers = DriverRepository(db)

    def get_driver(self, driver_id: int) -> Driver:
        driver = self.drivers.get_by_id(driver_id)

        if driver is None:
            raise DriverNotFoundError(
                f"Driver {driver_id} was not found."
            )

        return driver

    def get_drivers(
        self,
        search: str | None = None,
        status: str | None = None,
    ) -> list[Driver]:
        drivers = self.drivers.get_all()

        if search:
            search = search.strip().lower()

            drivers = [
                driver
                for driver in drivers
                if (
                    search in driver.name.lower()
                    or search in driver.phone.lower()
                    or search in driver.vehicle_type.lower()
                    or search in driver.vehicle_number.lower()
                )
            ]

        if status:
            status = status.strip().lower()

            drivers = [
                driver
                for driver in drivers
                if driver.status == status
            ]

        return drivers

    def create_driver(
        self,
        *,
        name: str,
        phone: str,
        vehicle_type: str,
        vehicle_number: str,
        status: str = "available",
    ) -> Driver:
        name = name.strip()
        phone = phone.strip()
        vehicle_type = vehicle_type.strip()
        vehicle_number = vehicle_number.strip()
        status = status.strip().lower()

        if not name:
            raise InvalidDriverDataError(
                "Driver name is required."
            )

        if not phone:
            raise InvalidDriverDataError(
                "Driver phone is required."
            )

        if not vehicle_type:
            raise InvalidDriverDataError(
                "Vehicle type is required."
            )

        if not vehicle_number:
            raise InvalidDriverDataError(
                "Vehicle number is required."
            )

        if status not in self.VALID_STATUSES:
            raise InvalidDriverStatusError(
                f"Invalid driver status: {status}."
            )

        if self.drivers.get_by_phone(phone):
            raise DuplicateDriverError(
                "A driver with this phone number already exists."
            )

        if self.drivers.get_by_vehicle_number(vehicle_number):
            raise DuplicateDriverError(
                "A driver with this vehicle number already exists."
            )

        driver = Driver(
            name=name,
            phone=phone,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            status=status,
        )

        try:
            self.db.add(driver)
            self.db.commit()
            self.db.refresh(driver)
            return driver

        except IntegrityError:
            self.db.rollback()
            raise DriverServiceError(
                "The driver could not be created."
            )

        except Exception:
            self.db.rollback()
            raise

    def update_driver(
        self,
        *,
        driver_id: int,
        name: str,
        phone: str,
        vehicle_type: str,
        vehicle_number: str,
        status: str,
    ) -> Driver:
        driver = self.get_driver(driver_id)

        name = name.strip()
        phone = phone.strip()
        vehicle_type = vehicle_type.strip()
        vehicle_number = vehicle_number.strip()
        status = status.strip().lower()

        if not name:
            raise InvalidDriverDataError(
                "Driver name is required."
            )

        if not phone:
            raise InvalidDriverDataError(
                "Driver phone is required."
            )

        if not vehicle_type:
            raise InvalidDriverDataError(
                "Vehicle type is required."
            )

        if not vehicle_number:
            raise InvalidDriverDataError(
                "Vehicle number is required."
            )

        if status not in self.VALID_STATUSES:
            raise InvalidDriverStatusError(
                f"Invalid driver status: {status}."
            )

        existing_phone = self.drivers.get_by_phone(phone)

        if (
            existing_phone is not None
            and existing_phone.id != driver.id
        ):
            raise DuplicateDriverError(
                "A driver with this phone number already exists."
            )

        existing_vehicle = self.drivers.get_by_vehicle_number(
            vehicle_number
        )

        if (
            existing_vehicle is not None
            and existing_vehicle.id != driver.id
        ):
            raise DuplicateDriverError(
                "A driver with this vehicle number already exists."
            )

        driver.name = name
        driver.phone = phone
        driver.vehicle_type = vehicle_type
        driver.vehicle_number = vehicle_number
        driver.status = status

        try:
            self.db.commit()
            self.db.refresh(driver)
            return driver

        except IntegrityError:
            self.db.rollback()
            raise DriverServiceError(
                "The driver could not be updated."
            )

        except Exception:
            self.db.rollback()
            raise

    def get_driver_deliveries(
        self,
        driver_id: int,
    ) -> list[Delivery]:
        self.get_driver(driver_id)
        return self.drivers.get_deliveries(driver_id)

    def get_driver_stats(
        self,
        driver_id: int,
    ) -> dict[str, object]:
        driver = self.get_driver(driver_id)
        deliveries = self.drivers.get_deliveries(driver.id)

        total = len(deliveries)

        delivered = sum(
            1
            for delivery in deliveries
            if delivery.status == "delivered"
        )

        pending = sum(
            1
            for delivery in deliveries
            if delivery.status == "pending"
        )

        in_progress = sum(
            1
            for delivery in deliveries
            if delivery.status in {
                "in_transit",
                "out_for_delivery",
            }
        )

        failed = sum(
            1
            for delivery in deliveries
            if delivery.status == "failed"
        )

        cancelled = sum(
            1
            for delivery in deliveries
            if delivery.status == "cancelled"
        )

        return {
            "total": total,
            "delivered": delivered,
            "pending": pending,
            "in_progress": in_progress,
            "failed": failed,
            "cancelled": cancelled,
            "last_delivery": (
                deliveries[0]
                if deliveries
                else None
            ),
        }

    def update_status(
        self,
        *,
        driver_id: int,
        status: str,
    ) -> Driver:
        driver = self.get_driver(driver_id)

        status = status.strip().lower()

        if status not in self.VALID_STATUSES:
            raise InvalidDriverStatusError(
                f"Invalid driver status: {status}."
            )

        driver.status = status

        try:
            self.db.commit()
            self.db.refresh(driver)
            return driver

        except Exception:
            self.db.rollback()
            raise