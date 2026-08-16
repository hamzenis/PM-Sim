# PM-Sim backend

This directory contains the canonical Python 3.13 backend and simulation engine.

## Run locally

Using `uv`:

```bash
uv sync
uv run python main.py create-demo
uv run python main.py serve --reload
uv run python main.py batch --scenario scenario_examples/basic_project.json --repetitions 100
```

The launcher applies Alembic migrations before database commands; the in-memory `batch` command
does not access or migrate the database. Running it without arguments remains an alias for
`serve`. The demo command creates a
professor, student, class, and published example scenario and prints development-only credentials.
Runtime settings are listed in `.env.example`.

Compare built-in strategies over the same deterministic seed range and save a CSV report with:

```bash
uv run python main.py batch \
  --scenario scenario_examples/basic_project.json \
  --strategy balanced --strategy quality-first \
  --employee-type junior_backend --team-size 3 \
  --repetitions 100 --initial-seed 1000 \
  --format csv --output /tmp/pm-sim-batch.csv --summary
```

`--output -` (the default) writes the selected `json` or `csv` format to standard output. Existing
files are protected unless `--force` is supplied. Omit `--employee-type` only for scenarios with
exactly one employee type. The optional summary is written to standard error, so report output can
be redirected safely.

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
