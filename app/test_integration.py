from datetime import datetime, timedelta, UTC

import pytest

from app.models import Delivery, DeliveryStatusHistory
from app.repositories import DeliveryRepository
from app.services.customer_service import CustomerService
from app.services.dashboard_service import DashboardService
from app.services.delivery_service import (
    DeliveryService,
    InvalidStatusError,
)
from app.services.driver_service import DriverService


def create_customer(db):
    return CustomerService(db).create_customer(
        name="Integration Customer",
        phone="09000001001",
        email="integration@example.com",
        address="Victoria Island, Lagos",
    )


def create_driver(
    db,
    *,
    name="Integration Driver",
    phone="09000002001",
    vehicle_number="INT-001",
):
    return DriverService(db).create_driver(
        name=name,
        phone=phone,
        vehicle_type="Motorcycle",
        vehicle_number=vehicle_number,
        status="available",
    )

def create_delivery(db, scheduled_at=None):
    customer = create_customer(db)
    driver = create_driver(db)

    service = DeliveryService(db)

    delivery = service.create_delivery(
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Ikeja, Lagos",
        delivery_address="Lekki, Lagos",
        scheduled_at=scheduled_at,
    )

    return delivery, customer, driver


def test_create_delivery_creates_tracking_number_and_initial_history(db):
    delivery, customer, driver = create_delivery(db)

    assert delivery.id is not None
    assert delivery.tracking_number.startswith("DLV-")
    assert delivery.customer_id == customer.id
    assert delivery.driver_id == driver.id
    assert delivery.status == "pending"

    history = DeliveryService(db).get_status_history(delivery.id)

    assert len(history) == 1
    assert history[0].status == "pending"
    assert history[0].delivery_id == delivery.id


def test_delivery_status_update_creates_history(db):
    delivery, _, _ = create_delivery(db)

    service = DeliveryService(db)

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="in_transit",
    )

    assert updated.status == "in_transit"

    history = service.get_status_history(delivery.id)

    assert len(history) == 2
    assert [item.status for item in history] == [
        "pending",
        "in_transit",
    ]


def test_delivery_status_update_to_delivered_sets_delivered_at(db):
    delivery, _, _ = create_delivery(db)

    service = DeliveryService(db)

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="in_transit",
    )

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="out_for_delivery",
    )

    updated = service.update_status(
        delivery_id=delivery.id,
        new_status="delivered",
    )

    assert updated.status == "delivered"
    assert updated.delivered_at is not None

    history = service.get_status_history(delivery.id)

    assert [item.status for item in history] == [
        "pending",
        "in_transit",
        "out_for_delivery",
        "delivered",
    ]


def test_invalid_status_transition_is_rejected(db):
    delivery, _, _ = create_delivery(db)

    service = DeliveryService(db)

    with pytest.raises(InvalidStatusError):
        service.update_status(
            delivery_id=delivery.id,
            new_status="delivered",
        )
        
def test_delayed_delivery_is_detected(db):
    scheduled_at = datetime.now(UTC) - timedelta(hours=1)

    delivery, _, _ = create_delivery(
        db,
        scheduled_at=scheduled_at,
    )

    service = DeliveryService(db)

    assert service.is_delayed(delivery) is True


def test_completed_delivery_is_not_delayed(db):
    scheduled_at = datetime.now(UTC) - timedelta(hours=1)

    delivery, _, _ = create_delivery(
        db,
        scheduled_at=scheduled_at,
    )

    service = DeliveryService(db)

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

    refreshed = service.get_delivery(delivery.id)

    assert service.is_delayed(refreshed) is False


def test_cancelled_delivery_is_not_delayed(db):
    scheduled_at = datetime.now(UTC) - timedelta(hours=1)

    delivery, _, _ = create_delivery(
        db,
        scheduled_at=scheduled_at,
    )

    service = DeliveryService(db)

    service.update_status(
        delivery_id=delivery.id,
        new_status="cancelled",
    )

    refreshed = service.get_delivery(delivery.id)

    assert service.is_delayed(refreshed) is False


def test_dashboard_reflects_delivery_statuses(db):
    customer = create_customer(db)
    pending_driver = create_driver(db)
    delivered_driver = create_driver(
        db,
        name="Integration Driver 2",
        phone="09000002002",
        vehicle_number="INT-002",
    )    
    
    service = DeliveryService(db)

    pending = service.create_delivery(
        customer_id=customer.id,
        driver_id=pending_driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        scheduled_at=datetime.now(UTC) + timedelta(hours=2),
    )

    delivered = service.create_delivery(
        customer_id=customer.id,
        driver_id=delivered_driver.id,
        pickup_address="Ikeja",
        delivery_address="Yaba",
        scheduled_at=datetime.now(UTC) + timedelta(hours=2),
    )

    service.update_status(
        delivery_id=delivered.id,
        new_status="in_transit",
    )
    service.update_status(
        delivery_id=delivered.id,
        new_status="out_for_delivery",
    )
    service.update_status(
        delivery_id=delivered.id,
        new_status="delivered",
    )

    dashboard = DashboardService(db).get_dashboard_data()

    assert dashboard["total"] == 2
    assert dashboard["pending"] == 1
    assert dashboard["delivered"] == 1
    assert dashboard["in_transit"] == 0
    assert dashboard["out_for_delivery"] == 0
    assert dashboard["failed"] == 0
    assert dashboard["cancelled"] == 0

    assert pending.id in [
        delivery.id
        for delivery in dashboard["recent_deliveries"]
    ]


def test_dashboard_counts_delayed_delivery(db):
    customer = create_customer(db)
    driver = create_driver(db)

    service = DeliveryService(db)

    service.create_delivery(
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Ikeja",
        delivery_address="Ikoyi",
        scheduled_at=datetime.now(UTC) - timedelta(hours=2),
    )

    dashboard = DashboardService(db).get_dashboard_data()

    assert dashboard["total"] == 1
    assert dashboard["delayed"] == 1
    assert len(dashboard["delayed_deliveries"]) == 1


def test_delivery_persists_through_repository(db):
    delivery, customer, driver = create_delivery(db)

    repository = DeliveryRepository(db)

    saved = repository.get_by_id(delivery.id)

    assert saved is not None
    assert saved.id == delivery.id
    assert saved.tracking_number == delivery.tracking_number
    assert saved.customer_id == customer.id
    assert saved.driver_id == driver.id


def test_delivery_relationships_are_persisted(db):
    delivery, customer, driver = create_delivery(db)

    saved = DeliveryService(db).get_delivery(delivery.id)

    assert saved.customer is not None
    assert saved.customer.id == customer.id

    assert saved.driver is not None
    assert saved.driver.id == driver.id

    history = DeliveryService(db).get_status_history(delivery.id)

    assert all(
        isinstance(item, DeliveryStatusHistory)
        for item in history
    )


def test_tracking_numbers_are_unique(db):
    customer = create_customer(db)
    first_driver = create_driver(db)
    second_driver = create_driver(
        db,
        name="Integration Driver 2",
        phone="09000002002",
        vehicle_number="INT-002",
    )
    service = DeliveryService(db)

    first = service.create_delivery(
        customer_id=customer.id,
        driver_id=first_driver.id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
    )

    second = service.create_delivery(
        customer_id=customer.id,
        driver_id=second_driver.id,
        pickup_address="Yaba",
        delivery_address="Ikoyi",
    )

    assert first.tracking_number != second.tracking_number