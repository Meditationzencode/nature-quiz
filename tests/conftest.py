import pytest
import app as quiz_app


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Every test runs against its own ephemeral DB and re-initialises schema.

    Prevents tests from touching the real scores.db and makes test order
    insensitive. Tests that need to seed the DB can still call
    quiz_app.init_db() explicitly; this fixture resets the init guard so
    that call re-runs against the new path.
    """
    monkeypatch.setattr(quiz_app, "DB_PATH", tmp_path / "scores.db")
    monkeypatch.setattr(quiz_app, "_db_initialized", False)
    yield


@pytest.fixture
def client():
    quiz_app.app.testing = True
    quiz_app.app.secret_key = "test-secret"
    return quiz_app.app.test_client()
