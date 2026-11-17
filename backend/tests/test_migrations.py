from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.core.db import Base
from tests.conftest import _alembic_config

EXPECTED_TABLES = {"users", "organizations", "organization_members", "cloud_accounts", "audit_logs"}


def test_schema_matches_models_and_is_reversible(db_url: str, scratch_engine) -> None:  # noqa: ANN001
    cfg = _alembic_config(db_url)
    # The session fixture already migrated to head; the models must produce no further diff.
    with scratch_engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert diff == [], f"models and migrations have drifted: {diff}"
        assert set(inspect(conn).get_table_names()) >= EXPECTED_TABLES

    command.downgrade(cfg, "base")
    with scratch_engine.connect() as conn:
        assert not (EXPECTED_TABLES & set(inspect(conn).get_table_names()))

    command.upgrade(cfg, "head")  # leave the schema in place for other tests
    with scratch_engine.connect() as conn:
        assert set(inspect(conn).get_table_names()) >= EXPECTED_TABLES
