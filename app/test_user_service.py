from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import verify_password
from app.services.user_service import (
    DuplicateUserError,
    InvalidUserDataError,
    InvalidUserRoleError,
    UserService,
)


def main() -> None:
    db = SessionLocal()

    try:
        # Clean up test user if it already exists.
        existing = db.scalar(
            select(User).where(
                User.email == "auth_test@example.com"
            )
        )

        if existing is not None:
            db.delete(existing)
            db.commit()

        service = UserService(db)

        # 1. Create user.
        user = service.create_user(
            email="  AUTH_TEST@EXAMPLE.COM  ",
            password="TestPassword123!",
            role="admin",
        )

        print("User created successfully.")
        print("ID:", user.id)
        print("Email:", user.email)
        print("Role:", user.role)
        print("Active:", user.is_active)

        # 2. Email should be normalized.
        assert user.email == "auth_test@example.com"

        # 3. Password must NOT be stored as plaintext.
        assert user.password_hash != "TestPassword123!"

        # 4. Correct password must verify.
        assert verify_password(
            "TestPassword123!",
            user.password_hash,
        )

        # 5. Wrong password must fail.
        assert not verify_password(
            "WrongPassword!",
            user.password_hash,
        )

        print("Password hashing/verification passed.")

        # 6. Duplicate email must fail.
        try:
            service.create_user(
                email="AUTH_TEST@example.com",
                password="AnotherPassword123!",
                role="viewer",
            )
            raise AssertionError(
                "Duplicate user creation should have failed."
            )

        except DuplicateUserError:
            print("Duplicate email validation passed.")

        # 7. Invalid role must fail.
        try:
            service.create_user(
                email="another@example.com",
                password="AnotherPassword123!",
                role="manager",
            )
            raise AssertionError(
                "Invalid role should have failed."
            )

        except InvalidUserRoleError:
            print("Invalid role validation passed.")

        # 8. Empty email must fail.
        try:
            service.create_user(
                email="   ",
                password="AnotherPassword123!",
                role="viewer",
            )
            raise AssertionError(
                "Empty email should have failed."
            )

        except InvalidUserDataError:
            print("Empty email validation passed.")

        # 9. Empty password must fail.
        try:
            service.create_user(
                email="another@example.com",
                password="",
                role="viewer",
            )
            raise AssertionError(
                "Empty password should have failed."
            )

        except InvalidUserDataError:
            print("Empty password validation passed.")

        print("All user service tests passed successfully.")

    finally:
        # Remove test data.
        test_user = db.scalar(
            select(User).where(
                User.email == "auth_test@example.com"
            )
        )

        if test_user is not None:
            db.delete(test_user)
            db.commit()

        db.close()


if __name__ == "__main__":
    main()