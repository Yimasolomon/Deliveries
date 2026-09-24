from sqlalchemy.orm import Session

from app.models import User
from app.repositories import UserRepository
from app.security import verify_password


class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> User | None:

        user = self.user_repository.get_by_email(email)

        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user