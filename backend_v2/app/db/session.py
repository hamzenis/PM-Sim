from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

DATABASE_URL = settings.database_url


def create_database_engine(
    database_url: str,
    *,
    sqlite_busy_timeout_ms: int = settings.sqlite_busy_timeout_ms,
    sqlite_wal: bool = settings.sqlite_wal,
    **engine_options: object,
) -> Engine:
    """Create a portable engine with safe SQLite classroom defaults."""
    if sqlite_busy_timeout_ms < 0:
        raise ValueError("SQLite busy timeout cannot be negative")
    url = make_url(database_url)
    connect_args = dict(engine_options.pop("connect_args", {}))
    if url.get_backend_name() == "sqlite":
        connect_args.setdefault("check_same_thread", False)
    database_engine = create_engine(database_url, connect_args=connect_args, **engine_options)
    if url.get_backend_name() == "sqlite":
        use_wal = sqlite_wal and url.database not in {None, "", ":memory:"}
        _configure_sqlite(
            database_engine,
            busy_timeout_ms=sqlite_busy_timeout_ms,
            use_wal=use_wal,
        )
    return database_engine


def _configure_sqlite(database_engine: Engine, *, busy_timeout_ms: int, use_wal: bool) -> None:
    @event.listens_for(database_engine, "connect")
    def set_sqlite_pragmas(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        if use_wal:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


engine = create_database_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_session() -> Generator[Session]:
    with SessionFactory() as session:
        yield session
