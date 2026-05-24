import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.testing = True
    flask_app.secret_key = "test-secret"
    return flask_app.test_client()
