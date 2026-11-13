
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Customer, User
from app.security import verify_password
from app.services.registration_service import (
    DuplicateRegistrationError,
    InvalidRegistrationDataError,
    RegistrationService,
)


def test_register_customer_creates_user_and_profile(db):
    service = RegistrationService(db)

    user = service.register_customer(
        name="Alice Johnson",
        email=" ALICE@EXAMPLE.COM ",
        password="TestPassword123!",
        phone="08022222222",
        address="Otukpo, Nigeria",
    )

    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.role == "customer"
    assert user.is_active is True

    assert user.password_hash != "TestPassword123!"
    assert verify_password(
        "TestPassword123!",
        user.password_hash,
    )

    customer = db.scalar(
        select(Customer).where(Customer.user_id == user.id)
    )

    assert customer is not None
    assert customer.name == "Alice Johnson"
    assert customer.email == "alice@example.com"
    assert customer.phone == "08022222222"
    assert customer.address == "Otukpo, Nigeria"
    assert customer.user is user
    assert user.customer is customer


def test_registration_always_assigns_customer_role(db):
    service = RegistrationService(db)

    user = service.register_customer(
        name="Bob Customer",
        email="bob@example.com",
        password="TestPassword123!",
        phone="08022222223",
        address="Makurdi, Nigeria",
    )

    assert user.role == "customer"


def test_registration_rejects_duplicate_user_email(db):
    service = RegistrationService(db)

    service.register_customer(
        name="Alice Johnson",
        email="alice@example.com",
        password="TestPassword123!",
        phone="08022222222",
        address="Otukpo, Nigeria",
    )

    try:
        service.register_customer(
            name="Another Customer",
            email="ALICE@EXAMPLE.COM",
            password="AnotherPassword123!",
            phone="08022222224",
            address="Makurdi, Nigeria",
        )
        assert False, "Duplicate email should have been rejected."
    except DuplicateRegistrationError:
        pass


def test_registration_rejects_duplicate_customer_email(db):
    db.add(
        Customer(
            name="Existing Customer",
            phone="08022222225",
            email="existing@example.com",
            address="Lagos, Nigeria",
        )
    )
    db.commit()

    service = RegistrationService(db)

    try:
        service.register_customer(
            name="New Customer",
            email="existing@example.com",
            password="TestPassword123!",
            phone="08022222226",
            address="Makurdi, Nigeria",
        )
        assert False, "Duplicate customer email should be rejected."
    except DuplicateRegistrationError:
        pass


def test_registration_rejects_duplicate_phone(db):
    db.add(
        Customer(
            name="Existing Customer",
            phone="08022222227",
            email="existing@example.com",
            address="Lagos, Nigeria",
        )
    )
    db.commit()

    service = RegistrationService(db)

    try:
        service.register_customer(
            name="New Customer",
            email="new@example.com",
            password="TestPassword123!",
            phone="08022222227",
            address="Makurdi, Nigeria",
        )
        assert False, "Duplicate phone should have been rejected."
    except DuplicateRegistrationError:
        pass


def test_registration_rejects_missing_required_data(db):
    service = RegistrationService(db)

    try:
        service.register_customer(
            name=" ",
            email="alice@example.com",
            password="TestPassword123!",
            phone="08022222222",
            address="Otukpo, Nigeria",
        )
        assert False, "Missing name should have been rejected."
    except InvalidRegistrationDataError:
        pass


def test_registration_rejects_invalid_email(db):
    service = RegistrationService(db)

    try:
        service.register_customer(
            name="Alice Johnson",
            email="not-an-email",
            password="TestPassword123!",
            phone="08022222222",
            address="Otukpo, Nigeria",
        )
        assert False, "Invalid email should have been rejected."
    except InvalidRegistrationDataError:
        pass


def test_registration_rolls_back_when_commit_fails(db, monkeypatch):
    service = RegistrationService(db)

    def fail_commit():
        raise IntegrityError(
            "INSERT",
            {},
            Exception("Simulated database constraint failure"),
        )

    monkeypatch.setattr(db, "commit", fail_commit)

    try:
        service.register_customer(
            name="Alice Johnson",
            email="alice@example.com",
            password="TestPassword123!",
            phone="08022222222",
            address="Otukpo, Nigeria",
        )
        assert False, "Failed commit should have raised an error."
    except DuplicateRegistrationError:
        pass

    assert db.scalar(
        select(User).where(User.email == "alice@example.com")
    ) is None

    assert db.scalar(
        select(Customer).where(Customer.email == "alice@example.com")
    ) is None
