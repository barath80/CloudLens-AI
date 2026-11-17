from fastapi import APIRouter, status

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, MembershipOut, MeResponse, RegisterRequest, TokenResponse, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession, settings: AppSettings) -> TokenResponse:
    return TokenResponse(access_token=AuthService(db, settings).register(data))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession, settings: AppSettings) -> TokenResponse:
    return TokenResponse(access_token=AuthService(db, settings).login(data))


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser, db: DbSession) -> MeResponse:
    memberships = UserRepository(db).memberships_for_user(user.id)
    return MeResponse(
        user=UserOut.model_validate(user),
        memberships=[
            MembershipOut(
                organization_id=m.organization_id,
                organization_name=m.organization.name,
                organization_slug=m.organization.slug,
                role=m.role,
            )
            for m in memberships
        ],
    )
