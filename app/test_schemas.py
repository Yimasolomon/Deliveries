from pydantic import ValidationError

from app.schemas import (
    CustomerCreate,
    DriverCreate,
    DeliveryCreate,
)


def test_customer_schema():
    customer = CustomerCreate(
        name="Alice Johnson",
        phone="08012345678",
        email="alice@example.com",
        address="Otukpo, Nigeria",
    )

    print("Customer schema:")
    print(customer.model_dump())


def test_driver_schema():
    driver = DriverCreate(
        name="David Driver",
        phone="08098765432",
        vehicle_type="Motorcycle",
        vehicle_number="ABC-123-XY",
    )

    print("Driver schema:")
    print(driver.model_dump())


def test_delivery_schema():
    delivery = DeliveryCreate(
        tracking_number="DLV-000001",
        customer_id=1,
        driver_id=1,
        pickup_address="Otukpo, Nigeria",
        delivery_address="Makurdi, Nigeria",
    )

    print("Delivery schema:")
    print(delivery.model_dump())

def test_invalid_customer():
    try:
        CustomerCreate(
            phone="08012345678",
            address="Otukpo, Nigeria",
        )
    except ValidationError as error:
        print("Invalid customer correctly rejected:")
        print(error)
    else:
        raise AssertionError("Invalid customer was accepted!")

if __name__ == "__main__":
    test_customer_schema()
    test_driver_schema()
    test_delivery_schema()
    test_invalid_customer()
    print("All schema tests passed successfully.")


from pydantic import ValidationError


def test_invalid_customer():
    try:
        CustomerCreate(
            phone="08012345678",
            address="Otukpo, Nigeria",
        )
    except ValidationError as error:
        print("Invalid customer correctly rejected:")
        print(error)
    else:
        raise AssertionError("Invalid customer was accepted!")
