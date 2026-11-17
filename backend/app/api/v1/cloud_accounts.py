import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import DbSession, OrgMember
from app.schemas.cloud_account import CloudAccountCreate, CloudAccountOut
from app.services.cloud_accounts import CloudAccountService

router = APIRouter(prefix="/organizations/{org_id}/cloud-accounts", tags=["cloud-accounts"])


@router.get("", response_model=list[CloudAccountOut])
def list_cloud_accounts(member: OrgMember, db: DbSession) -> list[CloudAccountOut]:
    return [CloudAccountOut.model_validate(a) for a in CloudAccountService(db).list(member)]


@router.post("", response_model=CloudAccountOut, status_code=status.HTTP_201_CREATED)
def create_cloud_account(data: CloudAccountCreate, member: OrgMember, db: DbSession) -> CloudAccountOut:
    return CloudAccountOut.model_validate(CloudAccountService(db).create(member, data))


@router.delete("/{account_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cloud_account(account_pk: uuid.UUID, member: OrgMember, db: DbSession) -> Response:
    CloudAccountService(db).delete(member, account_pk)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
