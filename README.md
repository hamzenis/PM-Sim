# PM-Sim

PM-Sim is a classroom project-management simulation for Frankfurt University of Applied
Sciences. Professors manage scenarios, classes, students, assignments, and results. Students
make weekly staffing and activity decisions while balancing scope, time, quality, and budget.

The repository contains two applications:

- `backend/`: Python 3.13, FastAPI, SQLAlchemy, Alembic, and the simulation engine.
- `frontend/`: React 19, Chakra UI, and Vite.

## Quick start

### Backend

```bash
cd backend
uv sync
uv run python main.py create-demo
uv run python main.py serve --reload
uv run python main.py batch --scenario scenario_examples/basic_project.json --repetitions 100
```

The backend command above remains the canonical batch invocation. As a convenience, after
installing the locked backend dependencies, run the same batch CLI from the repository root with:

```bash
uv run --project backend python scripts/run_batch.py \
  --scenario backend/scenario_examples/basic_project.json --repetitions 100
```

For a reproducible matrix, save a dependency-free JSON configuration such as
`experiment.json` at the repository root:

```json
{
  "scenarios": ["backend/scenario_examples/basic_project.json"],
  "strategies": ["balanced", "quality-first"],
  "team_compositions": [
    {
      "name": "three-junior-developers",
      "members": [{"employee_type_code": "junior_backend", "count": 3}]
    }
  ],
  "repetitions": 100,
  "initial_seed": 500,
  "output_formats": ["json", "csv", "html"],
  "output_root": "batch-experiments/example"
}
```

On Linux, run it from the repository root with:

```bash
uv run --project backend python scripts/run_batch.py --config experiment.json
```

Scenario and output paths are resolved relative to the configuration file. Experiment mode writes
atomic JSON and raw per-run CSV results beneath one filesystem-safe directory per
scenario/composition and, when `html` is requested, a self-contained `report.html` after those
underlying artifacts succeed. The report's baseline comparisons are balancing aids, not predictions
of student behavior. Experiment mode also writes a top-level `manifest.json`. It attempts every job
and exits nonzero if any fails. Existing artifacts
are protected; pass `--force` explicitly to replace them. Invocations without `--config` retain the
original argument-forwarding behavior.

The demo command creates these local-development accounts:

- professor: `professor` / `professor-password`
- student: `student` / `student-password`

The API is available at <http://127.0.0.1:8000>; OpenAPI documentation is at
<http://127.0.0.1:8000/docs>.

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite (normally <http://localhost:5173>). The development server proxies API
requests to the backend.

## Checks

```bash
cd backend
uv run ruff format --check .
uv run ruff check .
uv run pytest

cd ../frontend
npm test
npm run lint
npm run build
```

## Documentation map

Choose the path that matches what you are trying to do:

| Audience | Start here | Continue with |
| --- | --- | --- |
| Coding agents | [Repository agent guide](AGENTS.md) | [Backend agent guide](backend/AGENTS.md), [frontend agent guide](frontend/AGENTS.md), and the component documentation indexes |
| New contributors | [Contributing](CONTRIBUTING.md) | [Backend quick start](backend/README.md) or [frontend quick start](frontend/README.md) |
| Backend developers | [Backend documentation](backend/docs/README.md) | [Architecture](backend/docs/architecture.md), [development](backend/docs/development.md), and [testing](backend/docs/testing.md) |
| Frontend developers | [Frontend documentation](frontend/docs/README.md) | [Architecture](frontend/docs/architecture.md), [API integration](frontend/docs/api-integration.md), and [testing](frontend/docs/testing.md) |
| Operators | [Backend operations](backend/docs/sqlite-operations.md) | [Backend setup and configuration](backend/docs/development.md) and [frontend deployment](frontend/docs/deployment.md) |
| API consumers | [HTTP API](backend/docs/api.md) | [Authentication](frontend/docs/authentication.md) and [frontend adapters](frontend/docs/api-integration.md) |
| Scenario authors | [Authored scenario content](backend/docs/authored-content.md) | [Simulation engine](backend/docs/simulation-engine.md) and [data model](backend/docs/data-model.md) |
| Professors | [Professor workflows](frontend/docs/routing.md#professor-workflows) | [Scenario authoring](backend/docs/authored-content.md) |
| Students | [Student workflows](frontend/docs/routing.md#student-workflows) | [Accessibility and keyboard use](frontend/docs/accessibility.md) |

The two documentation indexes are the complete inventories for the
[`backend`](backend/docs/README.md) and [`frontend`](frontend/docs/README.md).
