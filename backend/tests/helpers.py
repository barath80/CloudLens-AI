from fastapi.testclient import TestClient

PASSWORD = "correct-horse-battery"


def register(client: TestClient, email: str, org: str = "Acme Corp") -> dict[str, str]:
    """Register a user (who becomes owner of a new org); return auth headers and ids."""
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Test User", "organization_name": org},
    )
    assert res.status_code == 201, res.text
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    return {"headers": headers, "org_id": me["memberships"][0]["organization_id"], "user_id": me["user"]["id"]}  # type: ignore[dict-item]


def account_payload(account_id: str = "123456789012") -> dict[str, str]:
    return {
        "name": "Production",
        "account_id": account_id,
        "role_arn": f"arn:aws:iam::{account_id}:role/CloudLensReadOnly",
    }
