# PM-Sim backend foundation

This directory contains the Python 3.13 rewrite. It deliberately coexists with the legacy
`backend/` while simulation behavior is reconstructed.

## Run locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The initial API exposes `GET /health` and `POST /api/scenarios/validate`. The simulation
package has no FastAPI, SQLAlchemy, or database imports and is shared by the API and batch
runner.

The default database URL is `sqlite:///./pm_sim.db`. Persistence code must use portable
SQLAlchemy types and migrations so PostgreSQL can replace SQLite later.
