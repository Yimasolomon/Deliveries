from datetime import datetime, timedelta, UTC

import pytest

from app.models import Customer, Driver, Delivery, DeliveryStatusHistory


@pytest.fixture
def seeded_customer_driver(route_client):
    client, session_factory = route_client

    db = session_factory()

    customer = Customer(
        name="Route Customer",
        phone="09100001001",
        email="route@example.com",
        address="Victoria Island, Lagos",
    )

    driver = Driver(
        name="Route Driver",
        phone="09100002001",
        vehicle_type="Motorcycle",
        vehicle_number="ROUTE-001",
        status="available",
    )

    db.add_all([customer, driver])
    db.commit()
    db.refresh(customer)
    db.refresh(driver)

    customer_id = customer.id
    driver_id = driver.id

    db.close()

    return client, session_factory, customer_id, driver_id


def test_health_route(route_client):
    client, _ = route_client

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirects_to_dashboard(route_client):
    client, _ = route_client

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_dashboard_requires_login(route_client):
    client, _ = route_client

    response = client.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_deliveries_route_loads(route_client):
    client, _ = route_client

    response = client.get("/deliveries")

    assert response.status_code == 200
    assert "Deliveries" in response.text


def test_deliveries_search_by_tracking_number(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-SEARCH-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.close()

    response = client.get(
        "/deliveries?search=DLV-SEARCH-001"
    )

    assert response.status_code == 200
    assert "DLV-SEARCH-001" in response.text
    assert "No deliveries found" not in response.text


def test_deliveries_search_by_customer_name(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-SEARCH-002",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.close()

    response = client.get(
        "/deliveries?search=Route%20Customer"
    )

    assert response.status_code == 200
    assert "DLV-SEARCH-002" in response.text
    assert "Route Customer" in response.text


def test_deliveries_search_by_address(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-SEARCH-003",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Unique Pickup Address",
        delivery_address="Unique Delivery Address",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.close()

    response = client.get(
        "/deliveries?search=Unique%20Delivery%20Address"
    )

    assert response.status_code == 200
    assert "DLV-SEARCH-003" in response.text
    assert "Unique Delivery Address" in response.text


def test_deliveries_status_filter(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    pending_delivery = Delivery(
        tracking_number="DLV-FILTER-PENDING",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    delivered_delivery = Delivery(
        tracking_number="DLV-FILTER-DELIVERED",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Yaba",
        delivery_address="Surulere",
        status="delivered",
    )

    db.add_all([
        pending_delivery,
        delivered_delivery,
    ])
    db.commit()
    db.close()

    response = client.get(
        "/deliveries?status=delivered"
    )

    assert response.status_code == 200
    assert "DLV-FILTER-DELIVERED" in response.text
    assert "DLV-FILTER-PENDING" not in response.text


def test_deliveries_search_and_status_filter(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    matching_delivery = Delivery(
        tracking_number="DLV-COMBINED-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Combined Search Address",
        status="delivered",
    )

    wrong_status = Delivery(
        tracking_number="DLV-COMBINED-002",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Combined Search Address",
        status="pending",
    )

    db.add_all([
        matching_delivery,
        wrong_status,
    ])
    db.commit()
    db.close()

    response = client.get(
        "/deliveries"
        "?search=Combined%20Search%20Address"
        "&status=delivered"
    )

    assert response.status_code == 200
    assert "DLV-COMBINED-001" in response.text
    assert "DLV-COMBINED-002" not in response.text


def test_deliveries_pagination(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    for number in range(1, 13):
        db.add(
            Delivery(
                tracking_number=f"DLV-PAGE-{number:03d}",
                customer_id=customer_id,
                driver_id=driver_id,
                pickup_address="Pagination Pickup",
                delivery_address="Pagination Delivery",
                status="pending",
            )
        )

    db.commit()
    db.close()

    first_page = client.get(
        "/deliveries?search=DLV-PAGE-"
    )

    assert first_page.status_code == 200

    # Page 1 contains the 10 newest matching deliveries.
    assert "DLV-PAGE-012" in first_page.text
    assert "DLV-PAGE-003" in first_page.text
    assert "DLV-PAGE-002" not in first_page.text
    assert "DLV-PAGE-001" not in first_page.text

    second_page = client.get(
        "/deliveries?search=DLV-PAGE-&page=2"
    )

    assert second_page.status_code == 200

    # Page 2 contains the remaining two deliveries.
    assert "DLV-PAGE-002" in second_page.text
    assert "DLV-PAGE-001" in second_page.text


def test_deliveries_pagination_preserves_filters(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    for number in range(1, 13):
        db.add(
            Delivery(
                tracking_number=f"DLV-FILTER-PAGE-{number:03d}",
                customer_id=customer_id,
                driver_id=driver_id,
                pickup_address="Pagination Pickup",
                delivery_address="Pagination Delivery",
                status="pending",
            )
        )

    db.commit()
    db.close()

    response = client.get(
        "/deliveries"
        "?search=Pagination%20Delivery"
        "&status=pending"
        "&page=2"
    )

    assert response.status_code == 200

    # The filter must still be present in pagination links.
    assert (
        "search=Pagination%20Delivery"
        in response.text
        or "search=Pagination+Delivery"
        in response.text
    )

    assert "status=pending" in response.text


def test_deliveries_page_beyond_last_page_uses_last_page(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    db.add(
        Delivery(
            tracking_number="DLV-LAST-PAGE-001",
            customer_id=customer_id,
            driver_id=driver_id,
            pickup_address="Ikeja",
            delivery_address="Lekki",
            status="pending",
        )
    )

    db.commit()
    db.close()

    response = client.get(
        "/deliveries?page=999"
    )

    assert response.status_code == 200
    assert "DLV-LAST-PAGE-001" in response.text


def test_new_delivery_form_loads(seeded_customer_driver):
    client, _, _, _ = seeded_customer_driver

    response = client.get("/deliveries/new")

    assert response.status_code == 200
    assert "New Delivery" in response.text
    assert "Route Customer" in response.text
    assert "Route Driver" in response.text


def test_create_delivery_route_persists_delivery(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    response = client.post(
        "/deliveries",
        data={
            "customer_id": str(customer_id),
            "driver_id": str(driver_id),
            "pickup_address": "Ikeja, Lagos",
            "delivery_address": "Lekki, Lagos",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    location = response.headers["location"]

    assert location.startswith("/deliveries/")

    delivery_id = int(location.rsplit("/", 1)[1])

    db = session_factory()

    delivery = db.get(Delivery, delivery_id)

    assert delivery is not None
    assert delivery.tracking_number.startswith("DLV-")
    assert delivery.customer_id == customer_id
    assert delivery.driver_id == driver_id
    assert delivery.status == "pending"

    history = (
        db.query(DeliveryStatusHistory)
        .filter(
            DeliveryStatusHistory.delivery_id == delivery_id
        )
        .all()
    )

    assert len(history) == 1
    assert history[0].status == "pending"

    db.close()


def test_delivery_detail_route_loads(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-ROUTE-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.add(
        DeliveryStatusHistory(
            delivery_id=delivery_id,
            status="pending",
            note="Initial status",
        )
    )

    db.commit()
    db.close()

    response = client.get(
        f"/deliveries/{delivery_id}"
    )

    assert response.status_code == 200
    assert "DLV-ROUTE-001" in response.text
    assert "Route Customer" in response.text


def test_delivery_detail_missing_returns_404(route_client):
    client, _ = route_client

    response = client.get("/deliveries/999999")

    assert response.status_code == 404
    assert "Delivery not found" in response.text


def test_delivery_status_route_updates_delivery(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-STATUS-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.add(
        DeliveryStatusHistory(
            delivery_id=delivery_id,
            status="pending",
        )
    )

    db.commit()
    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/status",
        data={
            "status": "in_transit",
            "note": "Driver has picked up the delivery.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/deliveries/{delivery_id}"
    )

    db = session_factory()

    updated = db.get(Delivery, delivery_id)

    assert updated.status == "in_transit"

    history = (
        db.query(DeliveryStatusHistory)
        .filter(
            DeliveryStatusHistory.delivery_id == delivery_id
        )
        .order_by(DeliveryStatusHistory.id)
        .all()
    )

    assert len(history) == 2
    assert history[0].status == "pending"
    assert history[1].status == "in_transit"
    assert history[1].note == (
        "Driver has picked up the delivery."
    )

    db.close()


def test_invalid_delivery_status_route_returns_400(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-INVALID-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.add(
        DeliveryStatusHistory(
            delivery_id=delivery_id,
            status="pending",
        )
    )

    db.commit()
    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/status",
        data={"status": "delivered"},
    )

    assert response.status_code == 400
    assert "Invalid" in response.text


def test_delete_delivery_route_cancels_delivery(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-CANCEL-ROUTE-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.add(
        DeliveryStatusHistory(
            delivery_id=delivery_id,
            status="pending",
        )
    )

    db.commit()
    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/deliveries"

    db = session_factory()

    cancelled = db.get(Delivery, delivery_id)

    assert cancelled is not None
    assert cancelled.status == "cancelled"

    history = (
        db.query(DeliveryStatusHistory)
        .filter(
            DeliveryStatusHistory.delivery_id == delivery_id
        )
        .order_by(DeliveryStatusHistory.id)
        .all()
    )

    assert len(history) == 2
    assert history[0].status == "pending"
    assert history[1].status == "cancelled"
    assert history[1].note == "Delivery cancelled by user."

    db.close()


def test_delete_delivery_route_rejects_terminal_delivery(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-CANCEL-ROUTE-002",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="delivered",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/delete"
    )

    assert response.status_code == 400
    assert "cannot be cancelled" in response.text.lower()


def test_customers_route_loads(route_client):
    client, _ = route_client

    response = client.get("/customers")

    assert response.status_code == 200
    assert "Customers" in response.text


def test_create_customer_route_persists_customer(route_client):
    client, session_factory = route_client

    response = client.post(
        "/customers",
        data={
            "name": "HTTP Customer",
            "phone": "09200001001",
            "email": "http@example.com",
            "address": "Yaba, Lagos",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    location = response.headers["location"]

    assert location.startswith("/customers/")

    customer_id = int(location.rsplit("/", 1)[1])

    db = session_factory()

    customer = db.get(Customer, customer_id)

    assert customer is not None
    assert customer.name == "HTTP Customer"
    assert customer.phone == "09200001001"
    assert customer.email == "http@example.com"
    assert customer.address == "Yaba, Lagos"

    db.close()


def test_customer_detail_route_loads(
    seeded_customer_driver,
):
    client, _, customer_id, _ = seeded_customer_driver

    response = client.get(
        f"/customers/{customer_id}"
    )

    assert response.status_code == 200
    assert "Route Customer" in response.text


def test_customer_detail_missing_returns_404(route_client):
    client, _ = route_client

    response = client.get("/customers/999999")

    assert response.status_code == 404
    assert "Customer not found" in response.text


def test_drivers_route_loads(route_client):
    client, _ = route_client

    response = client.get("/drivers")

    assert response.status_code == 200
    assert "Drivers" in response.text


def test_create_driver_route_persists_driver(route_client):
    client, session_factory = route_client

    response = client.post(
        "/drivers",
        data={
            "name": "HTTP Driver",
            "phone": "09300001001",
            "vehicle_type": "Motorcycle",
            "vehicle_number": "HTTP-001",
            "status": "available",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    location = response.headers["location"]

    assert location.startswith("/drivers/")

    driver_id = int(location.rsplit("/", 1)[1])

    db = session_factory()

    driver = db.get(Driver, driver_id)

    assert driver is not None
    assert driver.name == "HTTP Driver"
    assert driver.phone == "09300001001"
    assert driver.vehicle_type == "Motorcycle"
    assert driver.vehicle_number == "HTTP-001"
    assert driver.status == "available"

    db.close()


def test_edit_delivery_form_loads(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-EDIT-001",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id
    db.close()

    response = client.get(
        f"/deliveries/{delivery_id}/edit"
    )

    assert response.status_code == 200
    assert "Edit Delivery" in response.text
    assert "DLV-EDIT-001" in response.text
    assert "Route Customer" in response.text
    assert "Route Driver" in response.text


def test_edit_delivery_form_filters_drivers(
    seeded_customer_driver,
):
    client, session_factory, customer_id, current_driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    current_driver = db.get(Driver, current_driver_id)

    available_driver = Driver(
        name="Available Driver",
        phone="09100002002",
        vehicle_type="Motorcycle",
        vehicle_number="AVAILABLE-001",
        status="available",
    )

    busy_driver = Driver(
        name="Other Busy Driver",
        phone="09100002003",
        vehicle_type="Motorcycle",
        vehicle_number="BUSY-001",
        status="busy",
    )

    db.add_all([available_driver, busy_driver])
    db.commit()
    db.refresh(available_driver)
    db.refresh(busy_driver)

    current_driver.status = "busy"

    delivery = Delivery(
        tracking_number="DLV-EDIT-FILTER-001",
        customer_id=customer_id,
        driver_id=current_driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id

    db.close()

    response = client.get(
        f"/deliveries/{delivery_id}/edit"
    )

    assert response.status_code == 200

    assert "Route Driver" in response.text
    assert "Available Driver" in response.text

    assert "Other Busy Driver" not in response.text

    assert (
        f'value="{current_driver_id}"'
        in response.text
    )


def test_edit_delivery_missing_returns_404(route_client):
    client, _ = route_client

    response = client.get(
        "/deliveries/999999/edit"
    )

    assert response.status_code == 404
    assert "Delivery not found" in response.text


def test_edit_delivery_route_persists_changes(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    customer = Customer(
        name="Updated Route Customer",
        phone="09100003001",
        email="updated-route@example.com",
        address="Yaba, Lagos",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    updated_customer_id = customer.id

    delivery = Delivery(
        tracking_number="DLV-EDIT-002",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id
    original_tracking_number = delivery.tracking_number
    original_status = delivery.status

    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/edit",
        data={
            "customer_id": str(updated_customer_id),
            "driver_id": str(driver_id),
            "pickup_address": "Yaba, Lagos",
            "delivery_address": "Victoria Island, Lagos",
            "scheduled_at": "2026-09-15T14:30",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/deliveries/{delivery_id}"
    )

    db = session_factory()

    updated = db.get(Delivery, delivery_id)

    assert updated is not None
    assert updated.customer_id == updated_customer_id
    assert updated.driver_id == driver_id
    assert updated.pickup_address == "Yaba, Lagos"
    assert updated.delivery_address == "Victoria Island, Lagos"
    assert updated.scheduled_at == datetime(
        2026,
        9,
        15,
        14,
        30,
    )
    assert updated.tracking_number == original_tracking_number
    assert updated.status == original_status

    db.close()


def test_edit_delivery_rejects_missing_customer(
    seeded_customer_driver,
):
    client, session_factory, customer_id, driver_id = (
        seeded_customer_driver
    )

    db = session_factory()

    delivery = Delivery(
        tracking_number="DLV-EDIT-003",
        customer_id=customer_id,
        driver_id=driver_id,
        pickup_address="Ikeja",
        delivery_address="Lekki",
        status="pending",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    delivery_id = delivery.id
    db.close()

    response = client.post(
        f"/deliveries/{delivery_id}/edit",
        data={
            "customer_id": "999999",
            "driver_id": "",
            "pickup_address": "Ikeja",
            "delivery_address": "Lekki",
            "scheduled_at": "",
        },
    )

    assert response.status_code == 400
    assert "Customer 999999 was not found." in response.text


def test_security_headers(route_client):
    client, _ = route_client

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert (
        response.headers["Referrer-Policy"]
        == "strict-origin-when-cross-origin"
    )