import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite:///./pm_sim.db"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    cookie_secure: bool = False
    sqlite_busy_timeout_ms: int = 5000
    sqlite_wal: bool = True
    log_level: str = "info"

    @classmethod
    def from_environment(cls) -> "Settings":
        defaults = cls()
        settings = cls(
            database_url=os.getenv("DATABASE_URL", defaults.database_url),
            host=os.getenv("HOST", defaults.host),
            port=_integer("PORT", defaults.port),
            reload=_boolean("RELOAD", defaults.reload),
            cookie_secure=_boolean("COOKIE_SECURE", defaults.cookie_secure),
            sqlite_busy_timeout_ms=_integer(
                "SQLITE_BUSY_TIMEOUT_MS", defaults.sqlite_busy_timeout_ms
            ),
            sqlite_wal=_boolean("SQLITE_WAL", defaults.sqlite_wal),
            log_level=os.getenv("LOG_LEVEL", defaults.log_level).lower(),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL cannot be empty")
        if not self.host.strip():
            raise ValueError("HOST cannot be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        if self.sqlite_busy_timeout_ms < 0:
            raise ValueError("SQLITE_BUSY_TIMEOUT_MS cannot be negative")
        if self.log_level not in {"critical", "error", "warning", "info", "debug", "trace"}:
            raise ValueError("LOG_LEVEL is invalid")


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _integer(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error


settings = Settings.from_environment()
