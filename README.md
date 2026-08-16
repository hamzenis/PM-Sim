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
uv run python main.py batch scenario_examples/basic_project.json --repetitions 100
```

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
