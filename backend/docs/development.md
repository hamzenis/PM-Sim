# Development and local operation

## Requirements

- Python 3.13
- a standard Python virtual environment
- no container runtime

All commands in this document run from `backend`.

## First-time setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python main.py create-professor --username professor
python main.py --reload
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The launcher applies pending
Alembic migrations before executing its command. The default SQLite file is `pm_sim.db` in the
current directory.

## Runtime configuration

Configuration is read from environment variables. `.env.example` is a reference file; the
application does not implicitly load it. Export values in the shell or configure them in the
process manager.

Important settings include:

- `DATABASE_URL` (default `sqlite:///./pm_sim.db`);
- `HOST` and `PORT`;
- `RELOAD`;
- `COOKIE_SECURE` (enable behind HTTPS);
- `SESSION_LIFETIME_HOURS`;
- `SQLITE_BUSY_TIMEOUT_MS` and `SQLITE_WAL`;
- `LOG_LEVEL`.

Use `python main.py --help` for command-line overrides. `--no-migrate` is intended for controlled
diagnostics, not normal startup.

## Common commands

```bash
# Start the API
python main.py

# Development reload
python main.py --reload

# Create another professor interactively
python main.py create-professor --username another-professor

# Delete expired authentication sessions
python main.py cleanup-sessions

# Create a consistent timestamped SQLite backup
python main.py backup --output backups

# Inspect or apply migrations directly
alembic current
alembic upgrade head
alembic downgrade -1
```

Do not use `app/db/create_schema.py` for a persistent installation. Alembic is the authoritative
schema history.

## Checks

```bash
ruff format --check .
ruff check .
pytest
```

Run a focused test during development with, for example:

```bash
pytest tests/test_api.py -q
pytest tests/test_simulation_service.py -q
```

## Migration workflow

1. Change the SQLAlchemy model.
2. Add a new migration; never rewrite a migration that may already have been applied.
3. Verify upgrade from the preceding revision.
4. Verify downgrade where the operation is safely reversible.
5. Run the complete test suite.
6. Back up a real SQLite database before applying the migration outside development.

Migration files use portable types. Avoid relying on SQLite-only column behavior even while
SQLite remains the supported default.

## Transaction rules

- Application services own commits and rollbacks.
- HTTP routes call services and translate exceptions.
- An audit record belongs in the same transaction as its administrative change.
- Simulation turn creation and run advancement must be atomic.
- Published scenario revisions and simulation turns are append-only records.

## Troubleshooting

### `database is locked`

Confirm only one application process is using the SQLite database, WAL is enabled, and the
database is on a local filesystem. The supported launcher intentionally starts one worker.

### Login succeeds but the browser appears logged out

Ensure the frontend sends credentials and is either same-origin or proxied to the backend. Set
`COOKIE_SECURE=true` only when the browser reaches the service over HTTPS.

### The schema is missing a table or column

Run `alembic current` and `alembic upgrade head`. Do not repair a persistent database with
`create_all()`.

### A weekly turn returns `409`

The submitted run version is stale. Fetch the run again and review the decision against the new
state. Do not blindly repeat it with a new idempotency key.

### Restoring data

Stop the backend first. Follow `docs/sqlite-operations.md`; retain the current database until the
backup passes SQLite integrity checks and the application starts successfully.
