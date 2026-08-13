# PM-Sim backend

This directory contains the canonical Python 3.13 backend and simulation engine.

## Run locally

Using `uv`:

```bash
uv sync
uv run python main.py create-demo
uv run python main.py --reload
```

The launcher applies Alembic migrations before starting Uvicorn. The demo command creates a
professor, student, class, and published example scenario and prints development-only credentials.
Runtime settings are listed in `.env.example`.

The API currently covers authentication, professor-owned scenarios and classes, student
simulation runs, weekly decisions, submissions, and professor result audits. Interactive API
documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

## Documentation

Use the [backend documentation index](docs/README.md) for setup, architecture, API, engine,
authored-content, data-model, operations, testing, and decision guides.

## Checks

```bash
uv run ruff check .
uv run pytest
```
