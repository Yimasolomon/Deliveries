from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.session import add_session_middleware


app = FastAPI()

add_session_middleware(app)


@app.get("/session")
def session_test(request: Request):
    count = request.session.get("count", 0)
    count += 1

    request.session["count"] = count

    return {
        "count": count,
    }


client = TestClient(app)


def test_session_persists_between_requests():
    first_response = client.get("/session")

    assert first_response.status_code == 200
    assert first_response.json() == {"count": 1}

    second_response = client.get("/session")

    assert second_response.status_code == 200
    assert second_response.json() == {"count": 2}


if __name__ == "__main__":
    test_session_persists_between_requests()
    print("Session middleware test passed")