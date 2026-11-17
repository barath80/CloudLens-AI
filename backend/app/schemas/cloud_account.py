import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.cloud_account import CloudAccountStatus, CloudProvider

ACCOUNT_ID_PATTERN = r"^\d{12}$"
ROLE_ARN_PATTERN = r"^arn:aws[a-z-]*:iam::\d{12}:role/[\w+=,.@/-]+$"


class CloudAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    account_id: str = Field(pattern=ACCOUNT_ID_PATTERN, description="12-digit AWS account ID")
    role_arn: str = Field(pattern=ROLE_ARN_PATTERN, max_length=2048)


class CloudAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    provider: CloudProvider
    name: str
    account_id: str
    role_arn: str
    external_id: str
    status: CloudAccountStatus
    created_at: datetime
