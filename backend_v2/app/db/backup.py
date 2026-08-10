import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url


def backup_sqlite_database(
    database_url: str,
    output_directory: Path,
    *,
    now: datetime | None = None,
) -> Path:
    """Create a consistent SQLite backup using the standard library backup API."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in {None, "", ":memory:"}:
        raise ValueError("backup is available only for a file-based SQLite database")
    source_path = Path(url.database).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"database does not exist: {source_path}")
    output_directory = output_directory.expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S-%f")
    destination = output_directory / f"pm_sim-{timestamp}.db"
    if destination.exists():
        raise FileExistsError(f"backup already exists: {destination}")
    with (
        sqlite3.connect(source_path) as source,
        sqlite3.connect(destination) as target,
    ):
        source.backup(target)
    return destination
