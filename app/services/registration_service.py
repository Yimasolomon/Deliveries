from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Customer, User
from app.repositories import (
    CustomerRepository,
    UserRepository,
)
from app.security import hash_password


class RegistrationServiceError(Exception):
    """Base exception for customer registration errors."""


class DuplicateRegistrationError(RegistrationServiceError):
    """Raised when registration details already exist."""


class InvalidRegistrationDataError(RegistrationServiceError):
    """Raised when registration data is invalid."""


class RegistrationService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.customers = CustomerRepository(db)

    def register_customer(
        self,
        *,
        name: str,
        email: str,
        password: str,
        phone: str,
        address: str,
    ) -> User:
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        address = address.strip()

        if not all((name, email, password, phone, address)):
            raise InvalidRegistrationDataError(
                "All registration fields are required."
            )

        if "@" not in email:
            raise InvalidRegistrationDataError(
                "Please provide a valid email address."
            )

        if self.users.get_by_email(email):
            raise DuplicateRegistrationError(
                "An account with this email already exists."
            )

        if self.customers.get_by_email(email):
            raise DuplicateRegistrationError(
                "A customer profile with this email already exists."
            )

        if self.customers.get_by_phone(phone):
            raise DuplicateRegistrationError(
                "A customer profile with this phone number already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            role="customer",
        )

        customer = Customer(
            user=user,
            name=name,
            phone=phone,
            email=email,
            address=address,
        )

        try:
            self.users.add(user)
            self.customers.add(customer)

            self.db.commit()
            self.db.refresh(user)

            return user

        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateRegistrationError(
                "An account or customer profile with these details already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise
