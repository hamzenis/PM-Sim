import argparse
import getpass
import json
import logging
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from alembic.config import Config
from sqlalchemy import delete

from alembic import command
from app.auth.service import AuthenticationError, create_user
from app.batch.runner import report_to_dict, run_simulation_batch
from app.batch.strategies import built_in_strategy
from app.classes.service import assign_scenario, create_class, import_students
from app.config import Settings, settings
from app.db.backup import backup_sqlite_database
from app.db.models import AuthSessionRecord, UserRole
from app.db.session import SessionFactory
from app.scenarios.models import ScenarioDefinition
from app.scenarios.service import create_scenario, publish_revision

PROJECT_ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description="Run and manage the PM-Sim backend",
        epilog="Example:\n  python main.py serve --reload\n  python main.py --help",
        formatter_class=formatter,
    )
    subparsers = parser.add_subparsers(dest="command", title="commands", metavar="COMMAND")

    def command_parser(name: str, *, help: str, description: str, example: str):
        return subparsers.add_parser(
            name,
            help=help,
            description=description,
            epilog=f"Example:\n  {example}",
            formatter_class=formatter,
        )

    serve = command_parser(
        "serve",
        help="start the API server",
        description="Apply migrations and start Uvicorn.",
        example="python main.py serve --host 0.0.0.0 --port 8000",
    )
    serve.add_argument("--host", default=None, help="address on which the server listens")
    serve.add_argument(
        "--port", type=int, default=None, help="TCP port on which the server listens"
    )
    serve.add_argument(
        "--reload", action="store_true", help="reload after code changes (development only)"
    )
    _add_migration_option(serve)
    serve.set_defaults(handler=_handle_serve, migrate=True)

    professor = command_parser(
        "create-professor",
        help="create a professor account",
        description="Interactively create a professor account in the database.",
        example="python main.py create-professor --username instructor",
    )
    professor.add_argument("--username", help="username (prompted for when omitted)")
    _add_migration_option(professor)
    professor.set_defaults(handler=_handle_create_professor, migrate=True)

    demo = command_parser(
        "create-demo",
        help="create local demonstration data",
        description="Create fixed development users, a class, and an example scenario.",
        example="python main.py create-demo --scenario scenario_examples/basic_project.json",
    )
    demo.add_argument(
        "--scenario",
        type=Path,
        default=PROJECT_ROOT / "scenario_examples" / "basic_project.json",
        help="scenario JSON to load",
    )
    _add_migration_option(demo)
    demo.set_defaults(handler=_handle_create_demo, migrate=True)

    cleanup = command_parser(
        "cleanup-sessions",
        help="remove expired login sessions",
        description="Delete expired authentication sessions from the database.",
        example="python main.py cleanup-sessions",
    )
    _add_migration_option(cleanup)
    cleanup.set_defaults(handler=_handle_cleanup_sessions, migrate=True)

    backup = command_parser(
        "backup",
        help="create a consistent SQLite backup",
        description="Create a timestamped SQLite backup using the online backup API.",
        example="python main.py backup --output /srv/pm-sim-backups",
    )
    backup.add_argument("--output", type=Path, default=Path("backups"), help="backup directory")
    _add_migration_option(backup)
    backup.set_defaults(handler=_handle_backup, migrate=True)

    batch = command_parser(
        "batch",
        help="run deterministic simulations in memory",
        description="Run an authored scenario repeatedly without accessing the database.",
        example="python main.py batch scenario_examples/basic_project.json --repetitions 100",
    )
    batch.add_argument("scenario_path", type=Path, metavar="SCENARIO", help="scenario JSON file")
    batch.add_argument(
        "--strategy",
        default="balanced",
        choices=("development-first", "balanced", "quality-first", "overtime-heavy"),
        help="built-in decision strategy",
    )
    batch.add_argument(
        "--repetitions", type=int, default=100, help="number of simulations (default: 100)"
    )
    batch.add_argument("--initial-seed", type=int, default=0, help="first deterministic seed")
    batch.add_argument(
        "--employee-type", help="employee type code (defaults to the scenario's first)"
    )
    batch.set_defaults(handler=_handle_batch, migrate=False)

    # Compatibility: historically an empty argument list started the server.
    parser.set_defaults(
        handler=_handle_serve, migrate=True, host=None, port=None, reload=False, no_migrate=False
    )
    return parser


def _add_migration_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--no-migrate",
        action="store_true",
        help="skip Alembic migrations (controlled diagnostics only)",
    )


def _handle_serve(args: argparse.Namespace, _password_reader: Callable[[str], str]) -> int:
    start_server(settings, host=args.host, port=args.port, reload=args.reload or settings.reload)
    return 0


def _handle_create_professor(
    args: argparse.Namespace, password_reader: Callable[[str], str]
) -> int:
    return create_professor(args.username, password_reader=password_reader)


def _handle_create_demo(args: argparse.Namespace, _password_reader: Callable[[str], str]) -> int:
    return create_demo_data(args.scenario)


def _handle_cleanup_sessions(
    _args: argparse.Namespace, _password_reader: Callable[[str], str]
) -> int:
    return cleanup_sessions()


def _handle_backup(args: argparse.Namespace, _password_reader: Callable[[str], str]) -> int:
    return backup_database(args.output)


def _handle_batch(args: argparse.Namespace, _password_reader: Callable[[str], str]) -> int:
    try:
        scenario = ScenarioDefinition.model_validate(json.loads(args.scenario_path.read_text()))
        employee_type = args.employee_type or scenario.employee_types[0].code
        strategy = built_in_strategy(args.strategy, employee_type_code=employee_type)
        report = run_simulation_batch(
            scenario,
            strategy=strategy,
            repetitions=args.repetitions,
            initial_seed=args.initial_seed,
        )
    except (OSError, ValueError) as error:
        print(f"Could not run batch: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report_to_dict(report), indent=2))
    return 0


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
    if args.migrate and not args.no_migrate:
        run_migrations()
    return args.handler(args, password_reader)


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


def create_demo_data(scenario_path: Path) -> int:
    """Create a small local classroom for manual frontend tests."""
    try:
        definition = ScenarioDefinition.model_validate(json.loads(scenario_path.read_text()))
        with SessionFactory() as session:
            professor = create_user(
                session,
                username="professor",
                password="professor-password",
                role=UserRole.PROFESSOR,
            )
            course_class = create_class(session, professor_id=professor.id, name="Demo class")
            import_students(
                session,
                professor_id=professor.id,
                class_id=course_class.id,
                students=[("student", "student-password")],
            )
            revision = create_scenario(session, definition, owner_id=professor.id)
            publish_revision(
                session,
                revision.scenario_id,
                revision.revision_number,
                owner_id=professor.id,
            )
            assign_scenario(
                session,
                professor_id=professor.id,
                class_id=course_class.id,
                scenario_revision_id=revision.id,
            )
    except (OSError, ValueError, AuthenticationError) as error:
        print(f"Could not create demo data: {error}")
        return 2
    print("Created demo users: professor/professor-password and student/student-password")
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
