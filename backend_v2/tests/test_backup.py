import sqlite3
from datetime import UTC, datetime

import pytest

from app.db.backup import backup_sqlite_database


def test_sqlite_backup_contains_a_consistent_database_copy(tmp_path) -> None:
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE example (value TEXT NOT NULL)")
        connection.execute("INSERT INTO example(value) VALUES ('preserved')")
    destination = backup_sqlite_database(
        f"sqlite:///{source}",
        tmp_path / "backups",
        now=datetime(2026, 8, 10, 12, 30, tzinfo=UTC),
    )
    assert destination.name == "pm_sim-20260810-123000-000000.db"
    with sqlite3.connect(destination) as connection:
        assert connection.execute("SELECT value FROM example").fetchone() == ("preserved",)


@pytest.mark.parametrize("database_url", ["sqlite://", "sqlite:///:memory:", "postgresql://db"])
def test_backup_rejects_non_file_sqlite_databases(database_url: str, tmp_path) -> None:
    with pytest.raises(ValueError, match="file-based SQLite"):
        backup_sqlite_database(database_url, tmp_path)
