import pytest

from app.config import Settings


def test_settings_parse_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///custom.db")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("RELOAD", "yes")
    monkeypatch.setenv("COOKIE_SECURE", "on")
    monkeypatch.setenv("SESSION_LIFETIME_HOURS", "12")
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_MS", "1234")
    monkeypatch.setenv("SQLITE_WAL", "false")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = Settings.from_environment()
    assert settings == Settings(
        database_url="sqlite:///custom.db",
        host="0.0.0.0",
        port=9000,
        reload=True,
        cookie_secure=True,
        session_lifetime_hours=12,
        sqlite_busy_timeout_ms=1234,
        sqlite_wal=False,
        log_level="debug",
    )


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("PORT", "zero", "must be an integer"),
        ("RELOAD", "sometimes", "must be true or false"),
        ("LOG_LEVEL", "verbose", "LOG_LEVEL is invalid"),
        ("SESSION_LIFETIME_HOURS", "0", "must be positive"),
    ],
)
def test_invalid_environment_is_rejected(monkeypatch, name: str, value: str, message: str) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=message):
        Settings.from_environment()
