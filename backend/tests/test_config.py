import pytest
from pydantic import ValidationError

from app.core.config import Settings

DB = "postgresql+psycopg://u:p@127.0.0.1:5432/db"
GOOD_SECRET = "x" * 40


def make(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": DB, "jwt_secret_key": GOOD_SECRET}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_valid_settings() -> None:
    s = make(log_level="debug")
    assert s.log_level == "DEBUG"


def test_short_jwt_secret_rejected() -> None:
    with pytest.raises(ValidationError):
        make(jwt_secret_key="short")


def test_non_postgres_url_rejected() -> None:
    with pytest.raises(ValidationError):
        make(database_url="sqlite:///x.db")


def test_secrets_not_in_repr() -> None:
    text = repr(make())
    assert GOOD_SECRET not in text and "u:p@" not in text


def test_invalid_log_level_rejected() -> None:
    with pytest.raises(ValidationError):
        make(log_level="loud")
