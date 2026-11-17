import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Organization, OrganizationMember, Role, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def add_user(self, *, email: str, password_hash: str, full_name: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self.db.add(user)
        self.db.flush()
        return user

    def add_organization(self, name: str) -> Organization:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "org"
        slug = f"{base}-{uuid.uuid4().hex[:8]}"
        org = Organization(name=name, slug=slug)
        self.db.add(org)
        self.db.flush()
        return org

    def add_member(self, *, organization_id: uuid.UUID, user_id: uuid.UUID, role: Role) -> OrganizationMember:
        member = OrganizationMember(organization_id=organization_id, user_id=user_id, role=role)
        self.db.add(member)
        self.db.flush()
        return member

    def memberships_for_user(self, user_id: uuid.UUID) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .order_by(OrganizationMember.created_at)
        )
        members = list(self.db.scalars(stmt))
        for m in members:  # load organization eagerly for response mapping
            _ = m.organization
        return members

    def get_membership(self, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> OrganizationMember | None:
        return self.db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
