from sqlalchemy import create_engine

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
    
    from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User
from app.security import hash_password
from app.services.auth_service import AuthService


DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine
)


def setup_database():
    Base.metadata.create_all(bind=engine)


def test_authentication_success():

    setup_database()

    db = TestingSessionLocal()

    user = User(
        email="test@example.com",
        password_hash=hash_password("secret123"),
        is_active=True,
    )

    db.add(user)
    db.commit()

    auth_service = AuthService(db)

    result = auth_service.authenticate(
        "test@example.com",
        "secret123",
    )

    assert result is not None
    assert result.email == "test@example.com"

    db.close()


def test_wrong_password():

    setup_database()

    db = TestingSessionLocal()

    user = User(
        email="wrong@example.com",
        password_hash=hash_password("secret123"),
        is_active=True,
    )

    db.add(user)
    db.commit()

    auth_service = AuthService(db)

    result = auth_service.authenticate(
        "wrong@example.com",
        "incorrect",
    )

    assert result is None

    db.close()


def test_unknown_email():

    setup_database()

    db = TestingSessionLocal()

    auth_service = AuthService(db)

    result = auth_service.authenticate(
        "missing@example.com",
        "secret123",
    )

    assert result is None

    db.close()


def test_inactive_user():

    setup_database()

    db = TestingSessionLocal()

    user = User(
        email="inactive@example.com",
        password_hash=hash_password("secret123"),
        is_active=False,
    )

    db.add(user)
    db.commit()

    auth_service = AuthService(db)

    result = auth_service.authenticate(
        "inactive@example.com",
        "secret123",
    )

    assert result is None

    db.close()


if __name__ == "__main__":
    test_authentication_success()
    test_wrong_password()
    test_unknown_email()
    test_inactive_user()

    print("All authentication tests passed")
