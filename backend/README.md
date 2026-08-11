# PM-Sim backend

This directory contains the canonical Python 3.13 backend and simulation engine.

## Run locally

Using the standard Python tools:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python main.py create-professor --username professor
python main.py --reload
```

`python main.py` applies Alembic migrations and starts one Uvicorn process. Use
`python main.py --help` for host, port, reload, and migration options. Runtime settings are
listed in `.env.example`; export the values you want before starting the process. The project
also remains compatible with `uv sync` and `uv run python main.py`.

For a local end-to-end classroom test, use a fresh database and run `python main.py create-demo`.
This creates a professor, student, class, and published example scenario. The command prints its
development-only credentials when it succeeds.

Expired login sessions can be removed with `python main.py cleanup-sessions`.
Create a consistent SQLite backup with `python main.py backup --output backups`.

The API currently covers authentication, professor-owned scenarios and classes, student
simulation runs, weekly decisions, submissions, and professor result audits. Interactive API
documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

The simulation package has no FastAPI, SQLAlchemy, or database imports. `app.batch` uses that
same engine to run complete scenarios over many deterministic seeds. Its built-in
`development-first`, `balanced`, `quality-first`, and `overtime-heavy` strategies are simple
baselines for scenario balancing rather than authoritative student behavior. Reports can be
converted to dictionaries for JSON output or exported as CSV.

The default database URL is `sqlite:///./pm_sim.db`. Persistence code must use portable
SQLAlchemy types and migrations so PostgreSQL can replace SQLite later.
SQLite deployment, migration, backup, and restore procedures are documented in
[`docs/sqlite-operations.md`](docs/sqlite-operations.md).

## Documentation

- [`docs/adr/0001-authored-scenario-content.md`](docs/adr/0001-authored-scenario-content.md)
  records the approved presentation-only authored-content boundary.
- [`docs/architecture.md`](docs/architecture.md) explains the application layers, data model,
  transaction boundaries, and simulation lifecycle.
- [`docs/api.md`](docs/api.md) documents authentication, roles, HTTP endpoints, concurrency,
  idempotency, and response conventions.
- [`docs/development.md`](docs/development.md) covers the venv workflow, commands, migrations,
  tests, and troubleshooting without containers.
- [`docs/sqlite-operations.md`](docs/sqlite-operations.md) covers SQLite deployment, backup, and
  recovery procedures.

## Checks

```bash
uv run ruff check .
uv run pytest
```
