from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.repositories import UserRepository
from app.security import hash_password


class UserServiceError(Exception):
    """Base exception for user service errors."""


class DuplicateUserError(UserServiceError):
    """Raised when a user already exists."""


class InvalidUserDataError(UserServiceError):
    """Raised when user data is invalid."""


class InvalidUserRoleError(UserServiceError):
    """Raised when a user role is invalid."""


class UserService:
    VALID_ROLES = {
        "admin",
        "dispatcher",
        "viewer",
    }

    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)

        if user is None:
            raise UserServiceError(
                f"User {user_id} was not found."
            )

        return user

    def create_user(
        self,
        *,
        email: str,
        password: str,
        role: str = "viewer",
    ) -> User:
        email = email.strip().lower()
        role = role.strip().lower()

        if not email:
            raise InvalidUserDataError(
                "User email is required."
            )

        if not password:
            raise InvalidUserDataError(
                "User password is required."
            )

        if role not in self.VALID_ROLES:
            raise InvalidUserRoleError(
                f"Invalid user role: {role}."
            )

        existing_user = self.users.get_by_email(email)

        if existing_user is not None:
            raise DuplicateUserError(
                "A user with this email address already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            return user

        except IntegrityError:
            self.db.rollback()

            raise DuplicateUserError(
                "A user with this email address already exists."
            )

        except Exception:
            self.db.rollback()
            raise