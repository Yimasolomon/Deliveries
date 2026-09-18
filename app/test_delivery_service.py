import pytest

from datetime import datetime, UTC, timedelta

from app.models import Customer, Delivery, Driver
from app.services.delivery_service import (
    CustomerNotFoundError,
    DeliveryService,
    DriverUnavailableError,
    InvalidStatusError,
)

def create_delivery(
    db,
    *,
    status="pending",
    scheduled_at=None,
):
    customer = Customer(
        name="Test Customer",
        phone="08000000000",
        address="Test Address",
    )

    db.add(customer)
    db.flush()

    delivery = Delivery(
        tracking_number="TEST-001",
        customer_id=customer.id,
        pickup_address="Pickup Address",
        delivery_address="Delivery Address",
        status=status,
        scheduled_at=scheduled_at,
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


def test_delivery_is_delayed_when_schedule_has_passed(db):
    now = datetime.now(UTC)

    delivery = create_delivery(
        db,
        status="pending",
        scheduled_at=now - timedelta(hours=1),
    )

    service = DeliveryService(db)

    assert service.is_delayed(
        delivery,
        now=now,
    ) is True


def test_delivery_is_not_delayed_before_schedule(db):
    now = datetime.now(UTC)

    delivery = create_delivery(
        db,
        status="pending",
        scheduled_at=now + timedelta(hours=1),
    )

    service = DeliveryService(db)

    assert service.is_delayed(
        delivery,
        now=now,
    ) is False


def test_delivered_delivery_is_not_delayed(db):
    now = datetime.now(UTC)

    delivery = create_delivery(
        db,
        status="delivered",
        scheduled_at=now - timedelta(hours=1),
    )

    service = DeliveryService(db)

    assert service.is_delayed(
        delivery,
        now=now,
    ) is False


def test_failed_delivery_is_not_delayed(db):
    now = datetime.now(UTC)

    delivery = create_delivery(
        db,
        status="failed",
        scheduled_at=now - timedelta(hours=1),
    )

    service = DeliveryService(db)

    assert service.is_delayed(
        delivery,
        now=now,
    ) is False


def test_cancelled_delivery_is_not_delayed(db):
    now = datetime.now(UTC)

    delivery = create_delivery(
        db,
        status="cancelled",
        scheduled_at=now - timedelta(hours=1),
    )

    service = DeliveryService(db)

    assert service.is_delayed(
        delivery,
        now=now,
    ) is False

def test_update_delivery_changes_editable_fields(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    customer = Customer(
        name="Updated Customer",
        phone="08099999999",
        email="updated@example.com",
        address="New Customer Address",
    )
    db.add(customer)

    driver = Driver(
        name="Updated Driver",
        phone="08088888888",
        vehicle_type="Van",
        vehicle_number="VAN-002",
        status="available",
    )
    db.add(driver)

    db.commit()
    db.refresh(customer)
    db.refresh(driver)

    scheduled_at = datetime.now(UTC)

    updated = service.update_delivery(
        delivery_id=delivery.id,
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="New Pickup Address",
        delivery_address="New Delivery Address",
        scheduled_at=scheduled_at,
    )

    assert updated.customer_id == customer.id
    assert updated.driver_id == driver.id
    assert updated.pickup_address == "New Pickup Address"
    assert updated.delivery_address == "New Delivery Address"
    assert updated.scheduled_at == scheduled_at.replace(tzinfo=None)
    assert updated.tracking_number == delivery.tracking_number
    assert updated.status == "pending"


def test_update_delivery_rejects_missing_customer(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    with pytest.raises(CustomerNotFoundError):
        service.update_delivery(
            delivery_id=delivery.id,
            customer_id=999999,
            driver_id=None,
            pickup_address="Pickup",
            delivery_address="Delivery",
        )


def test_update_delivery_rejects_unavailable_new_driver(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    driver = Driver(
        name="Busy Driver",
        phone="08077777777",
        vehicle_type="Car",
        vehicle_number="CAR-002",
        status="busy",
    )

    db.add(driver)
    db.commit()
    db.refresh(driver)

    with pytest.raises(DriverUnavailableError):
        service.update_delivery(
            delivery_id=delivery.id,
            customer_id=delivery.customer_id,
            driver_id=driver.id,
            pickup_address="Pickup",
            delivery_address="Delivery",
        )


def test_update_delivery_allows_current_driver_when_not_available(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    driver = Driver(
        name="Current Driver",
        phone="08066666666",
        vehicle_type="Car",
        vehicle_number="CAR-003",
        status="available",
    )

    db.add(driver)
    db.commit()
    db.refresh(driver)

    delivery.driver_id = driver.id
    db.commit()

    driver.status = "busy"
    db.commit()

    updated = service.update_delivery(
        delivery_id=delivery.id,
        customer_id=delivery.customer_id,
        driver_id=driver.id,
        pickup_address="Updated Pickup",
        delivery_address="Updated Delivery",
    )

    assert updated.driver_id == driver.id
    assert updated.pickup_address == "Updated Pickup"

def test_cancel_delivery_changes_status_and_creates_history(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="pending",
    )

    cancelled = service.cancel_delivery(
        delivery_id=delivery.id,
        note="Customer requested cancellation.",
    )

    assert cancelled.status == "cancelled"

    history = service.get_status_history(delivery.id)

    assert len(history) >= 1

    cancelled_history = [
        entry
        for entry in history
        if entry.status == "cancelled"
    ]

    assert len(cancelled_history) == 1
    assert cancelled_history[0].note == (
        "Customer requested cancellation."
    )

def test_cancel_delivery_cannot_cancel_delivered_delivery(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="delivered",
    )

    with pytest.raises(InvalidStatusError):
        service.cancel_delivery(
            delivery_id=delivery.id,
        )


def test_cancel_delivery_cannot_cancel_failed_delivery(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="failed",
    )

    with pytest.raises(InvalidStatusError):
        service.cancel_delivery(
            delivery_id=delivery.id,
        )


def test_cancel_delivery_cannot_cancel_already_cancelled_delivery(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="cancelled",
    )

    with pytest.raises(InvalidStatusError):
        service.cancel_delivery(
            delivery_id=delivery.id,
        )



def test_update_status_allows_valid_transition(db):
    service = DeliveryService(db)

    delivery = create_delivery(db, status="pending")

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="in_transit",
        note="Driver picked up the delivery.",
    )

    assert updated.status == "in_transit"

    history = service.get_status_history(delivery.id)

    assert history[-1].status == "in_transit"
    assert history[-1].note == "Driver picked up the delivery."


def test_update_status_allows_full_valid_transition_chain(db):
    service = DeliveryService(db)

    delivery = create_delivery(db, status="pending")

    service.update_status(
        delivery.id,
        "in_transit",
    )

    service.update_status(
        delivery.id,
        "out_for_delivery",
    )

    updated = service.update_status(
        delivery.id,
        "delivered",
        note="Delivered to customer.",
    )

    assert updated.status == "delivered"
    assert updated.delivered_at is not None

    history = service.get_status_history(delivery.id)

    assert [entry.status for entry in history] == [
        "in_transit",
        "out_for_delivery",
        "delivered",
    ]

    assert history[-1].note == "Delivered to customer."


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        ("pending", "out_for_delivery"),
        ("pending", "delivered"),
        ("in_transit", "delivered"),
        ("out_for_delivery", "pending"),
    ],
)
def test_update_status_rejects_invalid_transition(
    db,
    current_status,
    new_status,
):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status=current_status,
    )

    with pytest.raises(InvalidStatusError):
        service.update_status(
            delivery_id=delivery.id,
            new_status=new_status,
        )

    db.refresh(delivery)

    assert delivery.status == current_status


@pytest.mark.parametrize(
    "terminal_status",
    [
        "delivered",
        "failed",
        "cancelled",
    ],
)
def test_update_status_rejects_changes_from_terminal_status(
    db,
    terminal_status,
):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status=terminal_status,
    )

    with pytest.raises(InvalidStatusError):
        service.update_status(
            delivery_id=delivery.id,
            new_status="pending",
        )

    db.refresh(delivery)

    assert delivery.status == terminal_status


def test_update_status_rejects_same_status(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="pending",
    )

    with pytest.raises(InvalidStatusError):
        service.update_status(
            delivery_id=delivery.id,
            new_status="pending",
        )

    db.refresh(delivery)

    assert delivery.status == "pending"


def test_update_status_rejects_unknown_status(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    with pytest.raises(InvalidStatusError):
        service.update_status(
            delivery_id=delivery.id,
            new_status="unknown_status",
        )

    db.refresh(delivery)

    assert delivery.status == "pending"


def test_update_status_normalizes_status_and_note(db):
    service = DeliveryService(db)

    delivery = create_delivery(db)

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status=" IN_TRANSIT ",
        note="  Driver picked up package.  ",
    )

    assert updated.status == "in_transit"

    history = service.get_status_history(delivery.id)

    assert history[-1].status == "in_transit"
    assert history[-1].note == "Driver picked up package."


def test_update_status_allows_failed_transition(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="in_transit",
    )

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="failed",
        note="Customer was unavailable.",
    )

    assert updated.status == "failed"

    history = service.get_status_history(delivery.id)

    assert history[-1].status == "failed"
    assert history[-1].note == "Customer was unavailable."


def test_update_status_allows_cancellation_from_active_delivery(db):
    service = DeliveryService(db)

    delivery = create_delivery(
        db,
        status="out_for_delivery",
    )

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="cancelled",
        note="Customer cancelled the order.",
    )

    assert updated.status == "cancelled"

    history = service.get_status_history(delivery.id)

    assert history[-1].status == "cancelled"
    assert history[-1].note == "Customer cancelled the order."

def test_terminal_delivery_releases_driver(db):
    service = DeliveryService(db)

    customer = Customer(
        name="Release Customer",
        phone="08000000001",
        address="Test Address",
    )

    driver = Driver(
        name="Release Driver",
        phone="08000000002",
        vehicle_type="Motorcycle",
        vehicle_number="REL-001",
        status="available",
    )

    db.add_all([customer, driver])
    db.commit()
    db.refresh(customer)
    db.refresh(driver)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(driver)
    assert driver.status == "busy"

    service.update_status(
        delivery_id=delivery.id,
        new_status="in_transit",
    )
    service.update_status(
        delivery_id=delivery.id,
        new_status="out_for_delivery",
    )
    service.update_status(
        delivery_id=delivery.id,
        new_status="delivered",
    )

    db.refresh(driver)

    assert driver.status == "available"


@pytest.mark.parametrize("terminal_status", ["failed", "cancelled"])
def test_failed_or_cancelled_delivery_releases_driver(db, terminal_status):
    service = DeliveryService(db)

    customer = Customer(
        name="Release Customer",
        phone="08000000003",
        address="Test Address",
    )

    driver = Driver(
        name="Release Driver",
        phone="08000000004",
        vehicle_type="Motorcycle",
        vehicle_number="REL-002",
        status="available",
    )

    db.add_all([customer, driver])
    db.commit()
    db.refresh(customer)
    db.refresh(driver)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(driver)
    assert driver.status == "busy"

    service.update_status(
        delivery_id=delivery.id,
        new_status="in_transit",
    )
    service.update_status(
        delivery_id=delivery.id,
        new_status="out_for_delivery",
    )
    service.update_status(
        delivery_id=delivery.id,
        new_status=terminal_status,
    )

    db.refresh(driver)

    assert driver.status == "available"

def test_reassign_active_delivery_updates_driver_statuses(db):
    service = DeliveryService(db)

    customer = Customer(
        name="Reassign Customer",
        phone="08000000005",
        address="Test Address",
    )

    old_driver = Driver(
        name="Old Driver",
        phone="08000000006",
        vehicle_type="Motorcycle",
        vehicle_number="REL-003",
        status="available",
    )

    new_driver = Driver(
        name="New Driver",
        phone="08000000007",
        vehicle_type="Motorcycle",
        vehicle_number="REL-004",
        status="available",
    )

    db.add_all([customer, old_driver, new_driver])
    db.commit()
    db.refresh(customer)
    db.refresh(old_driver)
    db.refresh(new_driver)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=old_driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(old_driver)
    db.refresh(new_driver)

    assert old_driver.status == "busy"
    assert new_driver.status == "available"

    updated = service.update_delivery(
        delivery_id=delivery.id,
        customer_id=customer.id,
        driver_id=new_driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(old_driver)
    db.refresh(new_driver)

    assert updated.driver_id == new_driver.id
    assert old_driver.status == "available"
    assert new_driver.status == "busy"


def test_unassign_active_delivery_releases_driver(db):
    service = DeliveryService(db)

    customer = Customer(
        name="Unassign Customer",
        phone="08000000008",
        address="Test Address",
    )

    driver = Driver(
        name="Unassign Driver",
        phone="08000000009",
        vehicle_type="Motorcycle",
        vehicle_number="REL-005",
        status="available",
    )

    db.add_all([customer, driver])
    db.commit()
    db.refresh(customer)
    db.refresh(driver)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(driver)
    assert driver.status == "busy"

    updated = service.update_delivery(
        delivery_id=delivery.id,
        customer_id=customer.id,
        driver_id=None,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    db.refresh(driver)

    assert updated.driver_id is None
    assert driver.status == "available"


def test_cannot_reassign_active_delivery_to_busy_driver(db):
    service = DeliveryService(db)

    customer = Customer(
        name="Busy Driver Customer",
        phone="08000000010",
        address="Test Address",
    )

    current_driver = Driver(
        name="Current Driver",
        phone="08000000011",
        vehicle_type="Motorcycle",
        vehicle_number="REL-006",
        status="available",
    )

    busy_driver = Driver(
        name="Busy Driver",
        phone="08000000012",
        vehicle_type="Motorcycle",
        vehicle_number="REL-007",
        status="busy",
    )

    db.add_all([customer, current_driver, busy_driver])
    db.commit()
    db.refresh(customer)
    db.refresh(current_driver)
    db.refresh(busy_driver)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=current_driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    with pytest.raises(DriverUnavailableError):
        service.update_delivery(
            delivery_id=delivery.id,
            customer_id=customer.id,
            driver_id=busy_driver.id,
            pickup_address="Ikeja",
            delivery_address="Lekki",
        )

    db.refresh(delivery)
    db.refresh(current_driver)
    db.refresh(busy_driver)

    assert delivery.driver_id == current_driver.id
    assert current_driver.status == "busy"
    assert busy_driver.status == "busy"    