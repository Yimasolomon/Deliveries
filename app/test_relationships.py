from app.database import SessionLocal
from app.models import Customer, Driver, Delivery


db = SessionLocal()

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
    tracking_number="DLV-000001",
    pickup_address="Otukpo, Nigeria",
    delivery_address="Makurdi, Nigeria",
    customer=customer,
    driver=driver,
)

db.add(delivery)
db.commit()
db.refresh(delivery)

print("Delivery ID:", delivery.id)
print("Tracking number:", delivery.tracking_number)
print("Customer:", delivery.customer.name)
print("Driver:", delivery.driver.name)

print("Customer deliveries:", len(customer.deliveries))
print("Driver deliveries:", len(driver.deliveries))

db.close()