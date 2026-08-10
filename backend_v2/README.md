# PM-Sim backend foundation

This directory contains the Python 3.13 rewrite. It deliberately coexists with the legacy
`backend/` while simulation behavior is reconstructed.

## Run locally

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The API currently covers authentication, professor-owned scenarios and classes, student
simulation runs, weekly decisions, submissions, and professor result audits. Interactive API
documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

The simulation package has no FastAPI, SQLAlchemy, or database imports. `app.batch` uses that
same engine to run complete scenarios over many deterministic seeds. Its built-in
`development-first`, `balanced`, `quality-first`, and `overtime-heavy` strategies are simple
baselines for scenario balancing rather than authoritative student behavior. Reports can be
converted to dictionaries for JSON output or exported as CSV.

Legacy behavior is being characterized before formulas are replaced. See
[`docs/legacy-behavior.md`](docs/legacy-behavior.md) for the observed execution order,
transcribed formulas, known differences, and parity rules.

The default database URL is `sqlite:///./pm_sim.db`. Persistence code must use portable
SQLAlchemy types and migrations so PostgreSQL can replace SQLite later.

## Checks

```bash
uv run ruff check .
uv run pytest
```
