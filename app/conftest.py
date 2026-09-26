import pytest

from app.models import User
from app.security import hash_password

@pytest.fixture
def authenticated_client(route_client):
    client, session_factory = route_client

    db = session_factory()

    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        role="admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.close()

    client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    return client, session_factory