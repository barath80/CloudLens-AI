import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.models import CloudAccount, OrganizationMember, Role
from app.repositories.audit import AuditRepository
from app.repositories.cloud_accounts import CloudAccountRepository
from app.schemas.cloud_account import CloudAccountCreate

WRITE_ROLES = {Role.OWNER, Role.ADMIN}


class CloudAccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CloudAccountRepository(db)
        self.audit = AuditRepository(db)

    def list(self, member: OrganizationMember) -> list[CloudAccount]:
        return self.repo.list(member.organization_id)

    def create(self, member: OrganizationMember, data: CloudAccountCreate) -> CloudAccount:
        self._require_write(member)
        if self.repo.get_by_account_id(member.organization_id, data.account_id):
            raise ConflictError("This AWS account is already registered", code="account_exists")
        try:
            account = self.repo.add(
                organization_id=member.organization_id,
                name=data.name,
                account_id=data.account_id,
                role_arn=data.role_arn,
            )
            self.audit.record(
                action="cloud_account.created",
                organization_id=member.organization_id,
                actor_user_id=member.user_id,
                target_type="cloud_account",
                target_id=str(account.id),
                details={"provider": "aws", "account_id": data.account_id},
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("This AWS account is already registered", code="account_exists") from exc
        return account

    def delete(self, member: OrganizationMember, account_pk: uuid.UUID) -> None:
        self._require_write(member)
        account = self.repo.get(member.organization_id, account_pk)
        if account is None:
            raise NotFoundError("Cloud account not found")
        self.repo.delete(account)
        self.audit.record(
            action="cloud_account.deleted",
            organization_id=member.organization_id,
            actor_user_id=member.user_id,
            target_type="cloud_account",
            target_id=str(account_pk),
        )
        self.db.commit()

    @staticmethod
    def _require_write(member: OrganizationMember) -> None:
        if member.role not in WRITE_ROLES:
            raise PermissionDeniedError("Your role does not permit managing cloud accounts")
