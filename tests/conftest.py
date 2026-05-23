import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as client:
        yield client


def start_quiz(client, difficulty="Easy", category="All"):
    client.post("/start", data={"difficulty": difficulty})
    client.post("/category", data={"category": category})
