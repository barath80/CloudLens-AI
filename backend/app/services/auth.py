from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Role
from app.repositories.audit import AuditRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

# Verified against when the email is unknown so login timing does not reveal which emails exist.
_DUMMY_HASH = hash_password("not-a-real-password")


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)
        self.audit = AuditRepository(db)

    def register(self, data: RegisterRequest) -> str:
        """Create a user, their organization and an owner membership in one transaction."""
        if self.users.get_by_email(data.email):
            raise ConflictError("An account with this email already exists", code="email_taken")
        try:
            user = self.users.add_user(
                email=data.email, password_hash=hash_password(data.password), full_name=data.full_name
            )
            org = self.users.add_organization(data.organization_name)
            self.users.add_member(organization_id=org.id, user_id=user.id, role=Role.OWNER)
            self.audit.record(
                action="user.registered",
                organization_id=org.id,
                actor_user_id=user.id,
                target_type="user",
                target_id=str(user.id),
            )
            self.db.commit()
        except IntegrityError as exc:  # concurrent registration with the same email
            self.db.rollback()
            raise ConflictError("An account with this email already exists", code="email_taken") from exc
        return create_access_token(user.id, self.settings)

    def login(self, data: LoginRequest) -> str:
        user = self.users.get_by_email(data.email)
        if user is None:
            verify_password(data.password, _DUMMY_HASH)
            raise AuthenticationError("Incorrect email or password")
        if not verify_password(data.password, user.password_hash) or not user.is_active:
            raise AuthenticationError("Incorrect email or password")
        self.audit.record(action="user.logged_in", actor_user_id=user.id, target_type="user", target_id=str(user.id))
        self.db.commit()
        return create_access_token(user.id, self.settings)
