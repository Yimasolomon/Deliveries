from app.database import SessionLocal
from app.models import Customer, Driver, Delivery
from app.repositories import (
    CustomerRepository,
    DriverRepository,
    DeliveryRepository,
)


def test_customer_repository(db):
    repository = CustomerRepository(db)

    customer = Customer(
        name="Repository Customer",
        phone="08011111111",
        email="repository@example.com",
        address="Makurdi, Nigeria",
    )

    created = repository.create(customer)

    assert created.id is not None

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.name == "Repository Customer"

    customers = repository.get_all()

    assert len(customers) >= 1

    print(f"Customer repository test passed. ID: {created.id}")


def test_driver_repository(db):
    repository = DriverRepository(db)

    driver = Driver(
        name="Repository Driver",
        phone="08022222222",
        vehicle_type="Motorcycle",
        vehicle_number="REP-001-XY",
    )

    created = repository.create(driver)

    assert created.id is not None

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.name == "Repository Driver"

    drivers = repository.get_all()

    assert len(drivers) >= 1

    print(f"Driver repository test passed. ID: {created.id}")


def test_delivery_repository(db):
    customer_repository = CustomerRepository(db)
    driver_repository = DriverRepository(db)
    delivery_repository = DeliveryRepository(db)

    customer = Customer(
        name="Delivery Customer",
        phone="08033333333",
        email="delivery@example.com",
        address="Otukpo, Nigeria",
    )

    driver = Driver(
        name="Delivery Driver",
        phone="08044444444",
        vehicle_type="Van",
        vehicle_number="DEL-001-XY",
    )

    customer = customer_repository.create(customer)
    driver = driver_repository.create(driver)

    delivery = Delivery(
        tracking_number="REP-DEL-000001",
        customer_id=customer.id,
        driver_id=driver.id,
        pickup_address="Otukpo, Nigeria",
        delivery_address="Makurdi, Nigeria",
    )

    created = delivery_repository.create(delivery)

    assert created.id is not None

    found = delivery_repository.get_by_id(created.id)

    assert found is not None
    assert found.tracking_number == "REP-DEL-000001"
    assert found.customer_id == customer.id
    assert found.driver_id == driver.id

    deliveries = delivery_repository.get_all()

    assert len(deliveries) >= 1

    print(f"Delivery repository test passed. ID: {created.id}")


if __name__ == "__main__":
    db = SessionLocal()

    try:
        test_customer_repository(db)
        test_driver_repository(db)
        test_delivery_repository(db)
        print("All repository tests passed successfully.")
    finally:
        db.close()

