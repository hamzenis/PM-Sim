from pathlib import Path

import pytest

import main as launcher
from app.config import Settings


def test_default_command_runs_migrations_and_starts_one_server(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(launcher, "run_migrations", lambda: calls.append("migrate"))
    monkeypatch.setattr(
        launcher,
        "start_server",
        lambda configuration, **options: calls.append((configuration, options)),
    )
    configured = Settings(host="127.0.0.1", port=8123)
    monkeypatch.setattr(launcher, "settings", configured)
    assert launcher.main([]) == 0
    assert calls == [
        "migrate",
        (configured, {"host": None, "port": None, "reload": False}),
    ]


def test_no_migrate_and_cli_server_options_are_forwarded(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        launcher,
        "run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("migration should be skipped")),
    )
    monkeypatch.setattr(
        launcher,
        "start_server",
        lambda _configuration, **options: calls.append(options),
    )
    assert (
        launcher.main(["serve", "--no-migrate", "--host", "0.0.0.0", "--port", "9000", "--reload"])
        == 0
    )
    assert calls == [{"host": "0.0.0.0", "port": 9000, "reload": True}]


def test_professor_password_confirmation_is_required(capsys) -> None:
    passwords = iter(["first-password", "second-password"])

    def reader(_prompt: str) -> str:
        return next(passwords)

    assert launcher.create_professor("professor", password_reader=reader) == 2
    assert "Passwords do not match" in capsys.readouterr().out


def test_backup_command_forwards_output_directory(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(
        launcher,
        "run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("backup must preserve the current schema")),
    )
    monkeypatch.setattr(
        launcher,
        "backup_database",
        lambda output: calls.append(output) or 0,
    )
    assert launcher.main(["backup", "--output", str(tmp_path)]) == 0
    assert calls == [tmp_path]


def test_demo_command_forwards_scenario_path(monkeypatch, tmp_path) -> None:
    scenario = tmp_path / "scenario.json"
    calls = []
    monkeypatch.setattr(launcher, "run_migrations", lambda: None)
    monkeypatch.setattr(launcher, "create_demo_data", lambda path: calls.append(path) or 0)
    assert launcher.main(["create-demo", "--scenario", str(scenario)]) == 0
    assert calls == [scenario]


@pytest.mark.parametrize(
    ("arguments", "operation_name", "operation_attribute"),
    [
        (["serve"], "serve", "start_server"),
        (["create-professor", "--username", "teacher"], "professor", "create_professor"),
        (["create-demo", "--scenario", "scenario.json"], "demo", "create_demo_data"),
        (["cleanup-sessions"], "cleanup", "cleanup_sessions"),
    ],
)
def test_database_commands_migrate_before_their_operation(
    monkeypatch, arguments, operation_name, operation_attribute
) -> None:
    calls = []
    monkeypatch.setattr(launcher, "run_migrations", lambda: calls.append("migrate"))
    monkeypatch.setattr(
        launcher,
        operation_attribute,
        lambda *args, **kwargs: calls.append(operation_name) or 0,
    )

    assert launcher.main(arguments, password_reader=lambda _prompt: "password") == 0
    assert calls == ["migrate", operation_name]


def test_migrate_command_only_runs_migrations(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(launcher, "run_migrations", lambda: calls.append("migrate"))
    assert launcher.main(["migrate"]) == 0
    assert calls == ["migrate"]


def test_help_does_not_run_migrations(monkeypatch) -> None:
    monkeypatch.setattr(
        launcher,
        "run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("help must not access the database")),
    )
    with pytest.raises(SystemExit) as error:
        launcher.main(["--help"])
    assert error.value.code == 0


@pytest.mark.parametrize(
    ("command", "foreign_option"),
    [
        ("serve", "--username"),
        ("create-professor", "--reload"),
        ("create-demo", "--output"),
        ("cleanup-sessions", "--scenario"),
        ("backup", "--no-migrate"),
        ("migrate", "--no-migrate"),
        ("batch", "--no-migrate"),
    ],
)
def test_parser_rejects_options_owned_by_other_commands(command, foreign_option) -> None:
    arguments = [command]
    if command == "batch":
        arguments.extend(("--scenario", "scenario.json"))
    arguments.append(foreign_option)
    with pytest.raises(SystemExit) as error:
        launcher.build_parser().parse_args(arguments)
    assert error.value.code == 2


def test_each_subcommand_has_examples_and_specific_help(capsys) -> None:
    parser = launcher.build_parser()
    for command in (
        "serve",
        "create-professor",
        "create-demo",
        "cleanup-sessions",
        "backup",
        "migrate",
        "batch",
    ):
        with pytest.raises(SystemExit) as error:
            parser.parse_args([command, "--help"])
        assert error.value.code == 0
        help_text = capsys.readouterr().out
        assert "Example:" in help_text
        assert command in help_text


def test_dispatch_uses_selected_parser_handler_without_migrating_batch(monkeypatch) -> None:
    calls = []
    parser = launcher.build_parser()
    selected = parser.parse_args(["batch", "--scenario", "scenario.json", "--repetitions", "3"])
    monkeypatch.setattr(parser, "parse_args", lambda _argv: selected)
    monkeypatch.setattr(launcher, "build_parser", lambda: parser)
    monkeypatch.setattr(
        launcher,
        "run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("no database")),
    )
    selected.handler = lambda args, _reader: calls.append(args.repetitions) or 7
    assert launcher.main([]) == 7
    assert calls == [3]


def test_batch_handler_runs_in_memory_without_migrating(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        launcher,
        "run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("batch must not access the database")),
    )
    scenario = Path(__file__).parent / "fixtures" / "batch_scenario.json"

    assert (
        launcher.main(["batch", "--scenario", str(scenario), "--repetitions", "1", "--summary"])
        == 0
    )
    captured = capsys.readouterr()
    assert '"summary"' in captured.out
    assert "balanced: seeds 0-0; completion" in captured.err


def test_batch_parser_defaults_and_paths() -> None:
    args = launcher.build_parser().parse_args(["batch", "--scenario", "example.json"])
    assert args.scenario == Path("example.json")
    assert args.strategies is None
    assert args.repetitions == 100
    assert args.initial_seed == 0
    assert args.team_size == 3
    assert args.format == "json"
    assert args.output == Path("-")
    assert args.force is False


def test_batch_parser_requires_scenario() -> None:
    with pytest.raises(SystemExit) as error:
        launcher.build_parser().parse_args(["batch"])
    assert error.value.code == 2


def test_batch_exports_selected_format_and_honors_force(tmp_path) -> None:
    scenario = Path(__file__).parent / "fixtures" / "batch_scenario.json"
    output = tmp_path / "report.csv"
    arguments = [
        "batch",
        "--scenario",
        str(scenario),
        "--repetitions",
        "2",
        "--strategy",
        "balanced",
        "--strategy",
        "quality-first",
        "--format",
        "csv",
        "--output",
        str(output),
    ]
    assert launcher.main(arguments) == 0
    assert "strategy" in output.read_text()
    assert launcher.main(arguments) == 1
    assert launcher.main([*arguments, "--force"]) == 0


def test_batch_invalid_configuration_returns_two() -> None:
    scenario = Path(__file__).parent / "fixtures" / "batch_scenario.json"
    assert launcher.main(["batch", "--scenario", str(scenario), "--repetitions", "0"]) == 2
