from datetime import datetime, timedelta

from app.database import SessionLocal
from app.database_init import init_db
from app.models import Customer, Driver, Delivery, DeliveryStatusHistory


def seed():
    init_db()

    db = SessionLocal()

    try:
        if db.query(Customer).count() > 0:
            print("Database already contains data.")
            return

        customers = [
            Customer(
                name="Chinedu Okafor",
                phone="08030000001",
                email="chinedu@example.com",
                address="Ikeja, Lagos",
            ),
            Customer(
                name="Amina Yusuf",
                phone="08030000002",
                email="amina@example.com",
                address="Lekki, Lagos",
            ),
            Customer(
                name="Tunde Balogun",
                phone="08030000003",
                email="tunde@example.com",
                address="Yaba, Lagos",
            ),
            Customer(
                name="Ngozi Eze",
                phone="08030000004",
                email="ngozi@example.com",
                address="Surulere, Lagos",
            ),
            Customer(
                name="David Adewale",
                phone="08030000005",
                email="david@example.com",
                address="Ikoyi, Lagos",
            ),
        ]

        drivers = [
            Driver(
                name="Emeka Driver",
                phone="08040000001",
                vehicle_type="Motorcycle",
                vehicle_number="LAG-101-AA",
            ),
            Driver(
                name="Samuel Driver",
                phone="08040000002",
                vehicle_type="Motorcycle",
                vehicle_number="LAG-102-BB",
            ),
            Driver(
                name="Ibrahim Driver",
                phone="08040000003",
                vehicle_type="Van",
                vehicle_number="LAG-103-CC",
            ),
            Driver(
                name="Daniel Driver",
                phone="08040000004",
                vehicle_type="Motorcycle",
                vehicle_number="LAG-104-DD",
            ),
        ]

        db.add_all(customers)
        db.add_all(drivers)
        db.commit()

        deliveries = [
            Delivery(
                tracking_number="DLV-000001",
                customer=customers[0],
                driver=drivers[0],
                pickup_address="Ikeja, Lagos",
                delivery_address="Victoria Island, Lagos",
                status="delivered",
                scheduled_at=datetime.utcnow() - timedelta(days=1),
                delivered_at=datetime.utcnow() - timedelta(hours=20),
            ),
            Delivery(
                tracking_number="DLV-000002",
                customer=customers[1],
                driver=drivers[1],
                pickup_address="Lekki, Lagos",
                delivery_address="Ikoyi, Lagos",
                status="out_for_delivery",
                scheduled_at=datetime.utcnow() + timedelta(hours=2),
            ),
            Delivery(
                tracking_number="DLV-000003",
                customer=customers[2],
                driver=drivers[2],
                pickup_address="Yaba, Lagos",
                delivery_address="Maryland, Lagos",
                status="in_transit",
                scheduled_at=datetime.utcnow() + timedelta(hours=4),
            ),
            Delivery(
                tracking_number="DLV-000004",
                customer=customers[3],
                driver=None,
                pickup_address="Surulere, Lagos",
                delivery_address="Gbagada, Lagos",
                status="pending",
                scheduled_at=datetime.utcnow() + timedelta(days=1),
            ),
            Delivery(
                tracking_number="DLV-000005",
                customer=customers[4],
                driver=drivers[3],
                pickup_address="Ikoyi, Lagos",
                delivery_address="Ajah, Lagos",
                status="failed",
                scheduled_at=datetime.utcnow() - timedelta(hours=5),
            ),
            Delivery(
                tracking_number="DLV-000006",
                customer=customers[0],
                driver=drivers[0],
                pickup_address="Ikeja, Lagos",
                delivery_address="Lagos Island, Lagos",
                status="pending",
                scheduled_at=datetime.utcnow() + timedelta(days=1),
            ),
        ]

        db.add_all(deliveries)
        db.commit()

        for delivery in deliveries:
            history = DeliveryStatusHistory(
                delivery_id=delivery.id,
                status=delivery.status,
                note="Initial delivery status",
            )

            db.add(history)

        db.commit()

        print("Database seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()