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
    assert launcher.main(["--no-migrate", "--host", "0.0.0.0", "--port", "9000", "--reload"]) == 0
    assert calls == [{"host": "0.0.0.0", "port": 9000, "reload": True}]


def test_professor_password_confirmation_is_required(capsys) -> None:
    passwords = iter(["first-password", "second-password"])

    def reader(_prompt: str) -> str:
        return next(passwords)

    assert launcher.create_professor("professor", password_reader=reader) == 2
    assert "Passwords do not match" in capsys.readouterr().out


def test_backup_command_forwards_output_directory(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(launcher, "run_migrations", lambda: None)
    monkeypatch.setattr(
        launcher,
        "backup_database",
        lambda output: calls.append(output) or 0,
    )
    assert launcher.main(["backup", "--output", str(tmp_path)]) == 0
    assert calls == [tmp_path]
