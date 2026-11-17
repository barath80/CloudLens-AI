import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.db import get_db
from app.main import create_app


def test_health_is_ok_and_leaks_nothing(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "CloudLens AI", "environment": "test"}


def test_database_health(client: TestClient) -> None:
    res = client.get("/api/v1/health/database")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "reachable"}


def test_ready(client: TestClient) -> None:
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready", "checks": {"database": "ok"}}


class _BrokenSession:
    def execute(self, *_: object, **__: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("password=hunter2 host=internal-db"))


@pytest.mark.parametrize("path", ["/api/v1/health/database", "/api/v1/health/ready"])
def test_unavailable_database_returns_503_without_details(path: str) -> None:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _BrokenSession()
    res = TestClient(app).get(path)
    assert res.status_code == 503
    assert "hunter2" not in res.text and "internal-db" not in res.text
