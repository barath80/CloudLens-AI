import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import decode_access_token
from app.models import OrganizationMember, User
from app.repositories.users import UserRepository

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DbSession,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    user = UserRepository(db).get(decode_access_token(credentials.credentials, settings))
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_org_member(org_id: uuid.UUID, user: CurrentUser, db: DbSession) -> OrganizationMember:
    """Resolve the caller's membership in the path organization.

    Non-members get 404 (not 403) so organization IDs cannot be probed across tenants.
    """
    member = UserRepository(db).get_membership(user_id=user.id, organization_id=org_id)
    if member is None:
        raise NotFoundError("Organization not found")
    return member


OrgMember = Annotated[OrganizationMember, Depends(get_org_member)]
