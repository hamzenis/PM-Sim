# PM-Sim

PM-Sim is a classroom project-management simulation for Frankfurt University of Applied
Sciences. Professors manage scenarios, classes, students, assignments, and results. Students
make weekly staffing and activity decisions while balancing scope, time, quality, and budget.

The repository contains two applications:

- `backend/`: Python 3.13, FastAPI, SQLAlchemy, Alembic, and the simulation engine.
- `frontend/`: React 18 and Chakra UI.

## Quick start

### Backend

```bash
cd backend
uv sync
uv run python main.py create-demo
uv run python main.py --reload
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
npm install
npm start
```

Open <http://127.0.0.1:3000>. The development server proxies API requests to the backend.

## Checks

```bash
cd backend
uv run ruff format --check .
uv run ruff check .
uv run pytest

cd ../frontend
CI=true npm test -- --runInBand
npm run build
```

See [`backend/README.md`](backend/README.md),
[`backend/docs/architecture.md`](backend/docs/architecture.md), and
[`frontend/README.md`](frontend/README.md) for more detail.
