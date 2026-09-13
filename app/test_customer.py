import pytest

from app.services.customer_service import (
    CustomerService,
    DuplicateCustomerError,
    InvalidCustomerDataError,
)

def test_create_customer(db):
    service = CustomerService(db)

    customer = service.create_customer(
        name="Test Customer",
        phone="09000000001",
        email="test@example.com",
        address="Test Address, Lagos",
    )

    assert customer.id is not None
    assert customer.name == "Test Customer"
    assert customer.phone == "09000000001"
    assert customer.email == "test@example.com"
    assert customer.address == "Test Address, Lagos"


def test_create_customer_rejects_duplicate_phone(db):
    service = CustomerService(db)

    service.create_customer(
        name="First Customer",
        phone="09000000002",
        email="first@example.com",
        address="Lagos",
    )

    with pytest.raises(DuplicateCustomerError):
        service.create_customer(
            name="Second Customer",
            phone="09000000002",
            email="second@example.com",
            address="Abuja",
        )


def test_create_customer_rejects_duplicate_email(db):
    service = CustomerService(db)

    service.create_customer(
        name="First Customer",
        phone="09000000003",
        email="duplicate@example.com",
        address="Lagos",
    )

    with pytest.raises(DuplicateCustomerError):
        service.create_customer(
            name="Second Customer",
            phone="09000000004",
            email="duplicate@example.com",
            address="Abuja",
        )


def test_create_customer_requires_name(db):
    service = CustomerService(db)

    with pytest.raises(InvalidCustomerDataError):
        service.create_customer(
            name="",
            phone="09000000005",
            email="valid@example.com",
            address="Lagos",
        )


def test_create_customer_requires_phone(db):
    service = CustomerService(db)

    with pytest.raises(InvalidCustomerDataError):
        service.create_customer(
            name="Test Customer",
            phone="",
            email="valid@example.com",
            address="Lagos",
        )


def test_create_customer_requires_address(db):
    service = CustomerService(db)

    with pytest.raises(InvalidCustomerDataError):
        service.create_customer(
            name="Test Customer",
            phone="09000000006",
            email="valid@example.com",
            address="",
        )


def test_update_customer(db):
    service = CustomerService(db)

    customer = service.create_customer(
        name="Original Name",
        phone="09000000007",
        email="original@example.com",
        address="Original Address",
    )

    updated = service.update_customer(
        customer_id=customer.id,
        name="Updated Name",
        phone="09000000008",
        email="updated@example.com",
        address="Updated Address",
    )

    assert updated.name == "Updated Name"
    assert updated.phone == "09000000008"
    assert updated.email == "updated@example.com"
    assert updated.address == "Updated Address"


def test_customer_search(db):
    service = CustomerService(db)

    service.create_customer(
        name="Alice Search",
        phone="09000000009",
        email="alice@example.com",
        address="Ikeja, Lagos",
    )

    service.create_customer(
        name="Bob Search",
        phone="09000000010",
        email="bob@example.com",
        address="Lekki, Lagos",
    )

    results = service.get_customers("Alice")

    assert len(results) == 1
    assert results[0].name == "Alice Search"


def test_customer_delivery_history_and_stats(db):
    from app.models import Delivery

    service = CustomerService(db)

    customer = service.create_customer(
        name="Delivery Customer",
        phone="09000000011",
        email="delivery@example.com",
        address="Lagos",
    )

    delivery_one = Delivery(
        tracking_number="TEST-000001",
        customer_id=customer.id,
        pickup_address="Pickup",
        delivery_address="Destination",
        status="delivered",
    )

    delivery_two = Delivery(
        tracking_number="TEST-000002",
        customer_id=customer.id,
        pickup_address="Pickup",
        delivery_address="Destination",
        status="pending",
    )

    db.add_all([delivery_one, delivery_two])
    db.commit()

    deliveries = service.get_customer_deliveries(customer.id)

    assert len(deliveries) == 2

    stats = service.get_customer_stats(customer.id)

    assert stats["total"] == 2
    assert stats["delivered"] == 1
    assert stats["pending"] == 1
    assert stats["failed"] == 0
    assert stats["cancelled"] == 0