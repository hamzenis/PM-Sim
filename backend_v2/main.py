import argparse
import getpass
import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from alembic.config import Config
from sqlalchemy import delete

from alembic import command
from app.auth.service import AuthenticationError, create_user
from app.config import Settings, settings
from app.db.backup import backup_sqlite_database
from app.db.models import AuthSessionRecord, UserRole
from app.db.session import SessionFactory

PROJECT_ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and manage the PM-Sim backend")
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=("serve", "create-professor", "cleanup-sessions", "backup"),
    )
    parser.add_argument("--host", default=None, help="Server address (serve only)")
    parser.add_argument("--port", type=int, default=None, help="Server port (serve only)")
    parser.add_argument("--reload", action="store_true", help="Reload after code changes")
    parser.add_argument("--no-migrate", action="store_true", help="Do not apply migrations")
    parser.add_argument("--username", help="Professor username")
    parser.add_argument("--output", type=Path, default=Path("backups"), help="Backup directory")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    password_reader: Callable[[str], str] = getpass.getpass,
) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not args.no_migrate:
        run_migrations()
    if args.command == "create-professor":
        return create_professor(args.username, password_reader=password_reader)
    if args.command == "cleanup-sessions":
        return cleanup_sessions()
    if args.command == "backup":
        return backup_database(args.output)
    start_server(
        settings,
        host=args.host,
        port=args.port,
        reload=args.reload or settings.reload,
    )
    return 0


def run_migrations() -> None:
    logging.getLogger(__name__).info("Applying database migrations")
    configuration = Config(PROJECT_ROOT / "alembic.ini")
    command.upgrade(configuration, "head")


def create_professor(
    username: str | None,
    *,
    password_reader: Callable[[str], str] = getpass.getpass,
) -> int:
    normalized_username = username or input("Professor username: ").strip()
    password = password_reader("Password: ")
    confirmation = password_reader("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match")
        return 2
    try:
        with SessionFactory() as session:
            user = create_user(
                session,
                username=normalized_username,
                password=password,
                role=UserRole.PROFESSOR,
            )
    except AuthenticationError as error:
        print(f"Could not create professor: {error}")
        return 2
    print(f"Created professor '{user.username}'")
    return 0


def cleanup_sessions() -> int:
    with SessionFactory() as session:
        result = session.execute(
            delete(AuthSessionRecord).where(AuthSessionRecord.expires_at <= datetime.now(UTC))
        )
        session.commit()
    print(f"Removed {result.rowcount} expired sessions")
    return 0


def backup_database(output_directory: Path) -> int:
    try:
        backup_path = backup_sqlite_database(settings.database_url, output_directory)
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        print(f"Could not create backup: {error}")
        return 2
    print(f"Created backup: {backup_path}")
    return 0


def start_server(
    configuration: Settings,
    *,
    host: str | None,
    port: int | None,
    reload: bool,
) -> None:
    selected_port = port if port is not None else configuration.port
    if not 1 <= selected_port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    uvicorn.run(
        "app.main:app",
        host=host or configuration.host,
        port=selected_port,
        reload=reload,
        workers=1,
        log_level=configuration.log_level,
    )


if __name__ == "__main__":
    raise SystemExit(main())
