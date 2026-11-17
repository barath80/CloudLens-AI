"""Test fixtures.

Tests run against a real PostgreSQL server (the `db` compose service) in dedicated databases, never
the development database. The server is located from DATABASE_URL; only the database name changes.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _ROOT / "backend"


def _server_url() -> str:
    url = os.environ.get("DATABASE_URL") or dotenv_values(_ROOT / ".env").get("DATABASE_URL")
    if not url:
        pytest.exit("DATABASE_URL is not set; start the db service and configure .env", returncode=2)
    return url


def _ensure_database(base_url: str, name: str) -> str:
    """Create database `name` on the same server if missing; return its SQLAlchemy URL."""
    url = make_url(base_url)
    admin = url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(admin, autocommit=True, connect_timeout=10) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{name}"')
    return url.set(database=name).render_as_string(hide_password=False)


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return cfg


_TEST_DB_URL = _ensure_database(_server_url(), "cloudlens_test")
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars-long"
os.environ["ENVIRONMENT"] = "test"

from app.core.db import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def db_url() -> str:
    return _TEST_DB_URL


@pytest.fixture(scope="session", autouse=True)
def _migrated_schema(db_url: str) -> Iterator[None]:
    cfg = _alembic_config(db_url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean_tables(_migrated_schema: None) -> None:
    with get_engine().begin() as conn:
        conn.execute(text("TRUNCATE audit_logs, cloud_accounts, organization_members, organizations, users CASCADE"))


@pytest.fixture
def db() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


@pytest.fixture
def client() -> Iterator["TestClient"]:  # noqa: F821
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def scratch_engine(db_url: str) -> Iterator["Engine"]:  # noqa: F821
    engine = create_engine(db_url)
    yield engine
    engine.dispose()
