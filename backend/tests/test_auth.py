from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Role, User
from tests.helpers import PASSWORD, register


def test_register_creates_user_org_and_owner_membership(client: TestClient, db: Session) -> None:
    ctx = register(client, "Alice@Example.com")
    me = client.get("/api/v1/auth/me", headers=ctx["headers"]).json()
    assert me["user"]["email"] == "alice@example.com"
    assert [m["role"] for m in me["memberships"]] == [Role.OWNER.value]
    user = db.scalar(select(User))
    assert user is not None and user.password_hash != PASSWORD and user.password_hash.startswith("$argon2")
    assert db.scalar(select(AuditLog).where(AuditLog.action == "user.registered")) is not None


def test_duplicate_email_conflict_is_case_insensitive(client: TestClient) -> None:
    register(client, "bob@example.com")
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "BOB@example.com", "password": PASSWORD, "full_name": "B", "organization_name": "X"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "email_taken"


def test_weak_password_rejected_with_uniform_error_shape(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "c@example.com", "password": "short", "full_name": "C", "organization_name": "X"},
    )
    assert res.status_code == 422
    body = res.json()["error"]
    assert body["code"] == "validation_error"
    assert any(d["field"] == "password" for d in body["details"])


def test_login_success_and_failures(client: TestClient) -> None:
    register(client, "dave@example.com")
    ok = client.post("/api/v1/auth/login", json={"email": "dave@example.com", "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["token_type"] == "bearer"

    wrong = client.post("/api/v1/auth/login", json={"email": "dave@example.com", "password": "wrong-password!"})
    unknown = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()  # no account enumeration


def test_me_requires_valid_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_expired_and_wrongly_signed_tokens_rejected(client: TestClient) -> None:
    ctx = register(client, "erin@example.com")
    expired = jwt.encode(
        {"sub": ctx["user_id"], "exp": datetime.now(UTC) - timedelta(minutes=1)},
        "test-secret-key-that-is-at-least-32-chars-long",
        "HS256",
    )
    forged = jwt.encode(
        {"sub": ctx["user_id"], "exp": datetime.now(UTC) + timedelta(hours=1)},
        "a-different-secret-of-sufficient-length!!",
        "HS256",
    )
    for token in (expired, forged):
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
