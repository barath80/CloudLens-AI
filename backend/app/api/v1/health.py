import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import AppSettings, DbSession
from app.schemas.health import DatabaseHealthResponse, HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


def _database_reachable(db: DbSession) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.warning("database health check failed", exc_info=True)
        return False


@router.get("", response_model=HealthResponse)
def health(settings: AppSettings) -> HealthResponse:
    """Liveness: the process is up. Does not touch dependencies."""
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.environment)


@router.get("/database", response_model=DatabaseHealthResponse)
def health_database(db: DbSession, response: Response) -> DatabaseHealthResponse:
    if _database_reachable(db):
        return DatabaseHealthResponse(status="ok", database="reachable")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return DatabaseHealthResponse(status="unavailable", database="unreachable")


@router.get("/ready", response_model=ReadinessResponse)
def health_ready(db: DbSession, response: Response) -> ReadinessResponse:
    """Readiness: all dependencies required to serve traffic are available."""
    checks = {"database": "ok" if _database_reachable(db) else "failed"}
    if "failed" in checks.values():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="not_ready", checks=checks)
    return ReadinessResponse(status="ready", checks=checks)
