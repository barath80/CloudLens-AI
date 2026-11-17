import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CloudProvider(enum.StrEnum):
    AWS = "aws"


class CloudAccountStatus(enum.StrEnum):
    PENDING = "pending"  # registered, cross-account role not yet verified
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


def _values(e: type[enum.Enum]) -> list[str]:
    return [m.value for m in e]


class CloudAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A customer cloud account reference. Never holds credentials: access is via STS AssumeRole."""

    __tablename__ = "cloud_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "account_id", name="uq_cloud_account_org_provider_account"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[CloudProvider] = mapped_column(
        Enum(CloudProvider, native_enum=False, length=20, values_callable=_values), default=CloudProvider.AWS
    )
    account_id: Mapped[str] = mapped_column(String(12))
    name: Mapped[str] = mapped_column(String(200))
    role_arn: Mapped[str] = mapped_column(String(2048))
    external_id: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[CloudAccountStatus] = mapped_column(
        Enum(CloudAccountStatus, native_enum=False, length=20, values_callable=_values),
        default=CloudAccountStatus.PENDING,
    )
