from app.database import SessionLocal
from app.models import Customer

db = SessionLocal()

customer = Customer(
    name="John doe",
    phone="08012345678",
    email="john@example.com",
    address="Otukpo, Nigeria",
)

db.add(customer)
db.commit()
db.refresh(customer)

print(f"Customer created with ID: {customer.id}")

db.close()