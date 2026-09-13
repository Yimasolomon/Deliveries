from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Customer, Driver, Delivery


def test_delivery_relationships():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        customer = Customer(
            name="Alice Johnson",
            phone="08022222222",
            email="alice@example.com",
            address="Otukpo, Nigeria",
        )

        driver = Driver(
            name="David Driver",
            phone="08033333333",
            vehicle_type="Motorcycle",
            vehicle_number="BEN-123-XY",
        )

        delivery = Delivery(
            tracking_number="TEST-DLV-000001",
            pickup_address="Otukpo, Nigeria",
            delivery_address="Makurdi, Nigeria",
            customer=customer,
            driver=driver,
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        assert delivery.id is not None
        assert delivery.tracking_number == "TEST-DLV-000001"

        assert delivery.customer is customer
        assert delivery.customer.name == "Alice Johnson"

        assert delivery.driver is driver
        assert delivery.driver.name == "David Driver"

        assert len(customer.deliveries) == 1
        assert customer.deliveries[0] is delivery

        assert len(driver.deliveries) == 1
        assert driver.deliveries[0] is delivery

    finally:
        db.close()
        engine.dispose()
