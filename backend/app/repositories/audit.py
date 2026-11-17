import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        action: str,
        organization_id: uuid.UUID | None = None,
        actor_user_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
        )
        self.db.add(entry)
        self.db.flush()
        return entry
