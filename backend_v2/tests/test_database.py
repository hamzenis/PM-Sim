import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.session import create_database_engine


def test_sqlite_engine_enables_foreign_keys_timeout_and_wal(tmp_path) -> None:
    database = tmp_path / "configured.db"
    engine = create_database_engine(
        f"sqlite:///{database}",
        sqlite_busy_timeout_ms=4321,
        sqlite_wal=True,
    )
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        assert connection.scalar(text("PRAGMA busy_timeout")) == 4321
        assert connection.scalar(text("PRAGMA journal_mode")) == "wal"
        assert connection.scalar(text("PRAGMA synchronous")) == 1
    engine.dispose()


def test_sqlite_foreign_key_violations_are_enforced(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'foreign-keys.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE child (parent_id INTEGER REFERENCES parent(id))"))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO child(parent_id) VALUES (99)"))
    engine.dispose()


def test_negative_busy_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        create_database_engine("sqlite://", sqlite_busy_timeout_ms=-1)
