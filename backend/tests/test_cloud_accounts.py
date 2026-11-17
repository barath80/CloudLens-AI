import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, OrganizationMember, Role
from tests.helpers import account_payload, register


def url(org_id: str, suffix: str = "") -> str:
    return f"/api/v1/organizations/{org_id}/cloud-accounts{suffix}"


def test_create_list_delete_with_audit(client: TestClient, db: Session) -> None:
    a = register(client, "a@example.com")
    res = client.post(url(a["org_id"]), json=account_payload(), headers=a["headers"])
    assert res.status_code == 201
    created = res.json()
    assert created["status"] == "pending" and created["external_id"].startswith("cl-")

    assert len(client.get(url(a["org_id"]), headers=a["headers"]).json()) == 1
    assert client.delete(url(a["org_id"], f"/{created['id']}"), headers=a["headers"]).status_code == 204
    assert client.get(url(a["org_id"]), headers=a["headers"]).json() == []

    actions = {e.action for e in db.scalars(select(AuditLog))}
    assert {"cloud_account.created", "cloud_account.deleted"} <= actions


def test_duplicate_account_conflict(client: TestClient) -> None:
    a = register(client, "a@example.com")
    client.post(url(a["org_id"]), json=account_payload(), headers=a["headers"])
    res = client.post(url(a["org_id"]), json=account_payload(), headers=a["headers"])
    assert res.status_code == 409 and res.json()["error"]["code"] == "account_exists"


def test_input_validation(client: TestClient) -> None:
    a = register(client, "a@example.com")
    bad = {"name": "x", "account_id": "12345", "role_arn": "not-an-arn"}
    res = client.post(url(a["org_id"]), json=bad, headers=a["headers"])
    assert res.status_code == 422


def test_unauthenticated_rejected(client: TestClient) -> None:
    assert client.get(url(str(uuid.uuid4()))).status_code == 401


# --- tenant isolation -------------------------------------------------------------------------


def test_cross_tenant_access_is_denied_and_indistinguishable_from_missing(client: TestClient) -> None:
    a = register(client, "a@example.com", org="Org A")
    b = register(client, "b@example.com", org="Org B")
    created = client.post(url(a["org_id"]), json=account_payload(), headers=a["headers"]).json()

    # B cannot list, create in, or delete from A's organization.
    for res in (
        client.get(url(a["org_id"]), headers=b["headers"]),
        client.post(url(a["org_id"]), json=account_payload("999999999999"), headers=b["headers"]),
        client.delete(url(a["org_id"], f"/{created['id']}"), headers=b["headers"]),
    ):
        assert res.status_code == 404
    # Same response as a non-existent organization, so org IDs cannot be probed.
    ghost = client.get(url(str(uuid.uuid4())), headers=b["headers"])
    assert ghost.status_code == 404

    # A's data is untouched; B's own org is empty and A's account is not reachable through B's org.
    assert len(client.get(url(a["org_id"]), headers=a["headers"]).json()) == 1
    assert client.get(url(b["org_id"]), headers=b["headers"]).json() == []
    assert client.delete(url(b["org_id"], f"/{created['id']}"), headers=b["headers"]).status_code == 404
    assert len(client.get(url(a["org_id"]), headers=a["headers"]).json()) == 1


def test_same_aws_account_may_be_registered_by_different_orgs(client: TestClient) -> None:
    a = register(client, "a@example.com", org="Org A")
    b = register(client, "b@example.com", org="Org B")
    assert client.post(url(a["org_id"]), json=account_payload(), headers=a["headers"]).status_code == 201
    assert client.post(url(b["org_id"]), json=account_payload(), headers=b["headers"]).status_code == 201


# --- role permissions -------------------------------------------------------------------------


def test_viewer_can_read_but_not_write(client: TestClient, db: Session) -> None:
    owner = register(client, "owner@example.com", org="Shared")
    viewer = register(client, "viewer@example.com", org="Viewer Own Org")
    db.add(
        OrganizationMember(
            organization_id=uuid.UUID(owner["org_id"]), user_id=uuid.UUID(viewer["user_id"]), role=Role.VIEWER
        )
    )
    db.commit()

    created = client.post(url(owner["org_id"]), json=account_payload(), headers=owner["headers"]).json()
    assert client.get(url(owner["org_id"]), headers=viewer["headers"]).status_code == 200
    assert (
        client.post(url(owner["org_id"]), json=account_payload("111111111111"), headers=viewer["headers"]).status_code
        == 403
    )
    assert client.delete(url(owner["org_id"], f"/{created['id']}"), headers=viewer["headers"]).status_code == 403
