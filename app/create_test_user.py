import os

from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


load_dotenv()

password = os.getenv("TEST_USER_PASSWORD")

if not password:
    raise RuntimeError("TEST_USER_PASSWORD must be set.")


db = SessionLocal()

user = User(
    email="admin@example.com",
    password_hash=hash_password(password),
    role="admin",
    is_active=True,
)

db.add(user)
db.commit()
db.refresh(user)

print("Created user:")
print("ID:", user.id)
print("Email:", user.email)

db.close()