from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Customer, Delivery
from app.repositories import CustomerRepository


class CustomerServiceError(Exception):
    """Base exception for customer service errors."""


class CustomerNotFoundError(CustomerServiceError):
    """Raised when a customer cannot be found."""


class DuplicateCustomerError(CustomerServiceError):
    """Raised when a customer already exists."""


class InvalidCustomerDataError(CustomerServiceError):
    """Raised when customer data is invalid."""


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.customers = CustomerRepository(db)

    def get_customer(
        self,
        customer_id: int,
    ) -> Customer:
        customer = self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                f"Customer {customer_id} was not found."
            )

        return customer

    def get_customer_deliveries(self, customer_id: int) -> list[Delivery]:
        self.get_customer(customer_id)
        return self.customers.get_deliveries(customer_id)

    def get_customers(
        self,
        search: str | None = None,
    ) -> list[Customer]:
        customers = self.customers.get_all()

        if not search:
            return customers

        search = search.strip().lower()

        return [
            customer
            for customer in customers
            if (
                search in customer.name.lower()
                or search in customer.phone.lower()
                or (
                    customer.email
                    and search in customer.email.lower()
                )
                or search in customer.address.lower()
            )
        ]

    def create_customer(
        self,
        *,
        name: str,
        phone: str,
        email: str | None,
        address: str,
    ) -> Customer:
        name = name.strip()
        phone = phone.strip()
        address = address.strip()

        if email is not None:
            email = email.strip().lower()

            if not email:
                email = None

        if not name:
            raise InvalidCustomerDataError(
                "Customer name is required."
            )

        if not phone:
            raise InvalidCustomerDataError(
                "Customer phone is required."
            )

        if not address:
            raise InvalidCustomerDataError(
                "Customer address is required."
            )

        existing_phone = self.customers.get_by_phone(phone)

        if existing_phone is not None:
            raise DuplicateCustomerError(
                "A customer with this phone number "
                "already exists."
            )

        if email is not None:
            existing_email = self.customers.get_by_email(email)

            if existing_email is not None:
                raise DuplicateCustomerError(
                    "A customer with this email address "
                    "already exists."
                )

        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            address=address,
        )

        try:
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)

            return customer

        except IntegrityError:
            self.db.rollback()

            raise CustomerServiceError(
                "The customer could not be created."
            )

        except Exception:
            self.db.rollback()
            raise

    def update_customer(
        self,
        *,
        customer_id: int,
        name: str,
        phone: str,
        email: str | None,
        address: str,
    ) -> Customer:
        customer = self.get_customer(customer_id)

        name = name.strip()
        phone = phone.strip()
        address = address.strip()

        if email is not None:
            email = email.strip().lower()

            if not email:
                email = None

        if not name:
            raise InvalidCustomerDataError(
                "Customer name is required."
            )

        if not phone:
            raise InvalidCustomerDataError(
                "Customer phone is required."
            )

        if not address:
            raise InvalidCustomerDataError(
                "Customer address is required."
            )

        existing_phone = self.customers.get_by_phone(phone)

        if (
            existing_phone is not None
            and existing_phone.id != customer.id
        ):
            raise DuplicateCustomerError(
                "A customer with this phone number "
                "already exists."
            )

        if email is not None:
            existing_email = self.customers.get_by_email(email)

            if (
                existing_email is not None
                and existing_email.id != customer.id
            ):
                raise DuplicateCustomerError(
                    "A customer with this email address "
                    "already exists."
                )

        customer.name = name
        customer.phone = phone
        customer.email = email
        customer.address = address

        try:
            self.db.commit()
            self.db.refresh(customer)

            return customer

        except IntegrityError:
            self.db.rollback()

            raise CustomerServiceError(
                "The customer could not be updated."
            )

        except Exception:
            self.db.rollback()
            raise

    def get_customer_stats(self, customer_id: int) -> dict[str, object]:
        customer = self.get_customer(customer_id)
        deliveries = self.customers.get_deliveries(customer.id)

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
            if delivery.status in {"in_transit", "out_for_delivery"}
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
            "last_delivery": deliveries[0] if deliveries else None,
        }