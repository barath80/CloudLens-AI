import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CloudAccount, CloudProvider


class CloudAccountRepository:
    """Every query takes organization_id: callers cannot read another tenant's rows by accident."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, organization_id: uuid.UUID) -> list[CloudAccount]:
        stmt = (
            select(CloudAccount)
            .where(CloudAccount.organization_id == organization_id)
            .order_by(CloudAccount.created_at)
        )
        return list(self.db.scalars(stmt))

    def get(self, organization_id: uuid.UUID, account_pk: uuid.UUID) -> CloudAccount | None:
        return self.db.scalar(
            select(CloudAccount).where(CloudAccount.organization_id == organization_id, CloudAccount.id == account_pk)
        )

    def get_by_account_id(self, organization_id: uuid.UUID, account_id: str) -> CloudAccount | None:
        return self.db.scalar(
            select(CloudAccount).where(
                CloudAccount.organization_id == organization_id,
                CloudAccount.provider == CloudProvider.AWS,
                CloudAccount.account_id == account_id,
            )
        )

    def add(self, *, organization_id: uuid.UUID, name: str, account_id: str, role_arn: str) -> CloudAccount:
        account = CloudAccount(
            organization_id=organization_id,
            provider=CloudProvider.AWS,
            name=name,
            account_id=account_id,
            role_arn=role_arn,
            external_id=f"cl-{secrets.token_urlsafe(24)}",
        )
        self.db.add(account)
        self.db.flush()
        return account

    def delete(self, account: CloudAccount) -> None:
        self.db.delete(account)
        self.db.flush()
