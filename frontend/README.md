# PM-Sim frontend

The frontend is a React 18 application using Chakra UI. It provides professor workflows for
scenarios, classes, students, results, and audit history, plus the complete student simulation
workflow.

## Requirements

- Node.js 20
- npm
- the PM-Sim backend running on `http://127.0.0.1:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally <http://localhost:5173>). The development server proxies
relative `/api` requests to the backend.

For a separate API origin, copy `.env.template` to `.env` and set:

```bash
VITE_API_BASE_URL=https://api.example.test
```

The backend must explicitly allow the frontend origin when the applications are not served from
the same origin.

## Application routes

- `/login`: authentication.
- `/scenarios`: professor scenario lifecycle or student assignments and runs.
- `/simulations/:run_id`: weekly student decisions, history, and final result.
- `/classes`: professor class, student, assignment, and result management.
- `/classes/:class_id/results/:run_id`: professor run audit.
- `/audit`: professor administrative history.
- `/change-password`: authenticated password change.

All HTTP requests go through `src/api/client.js`. Authentication uses an HTTP-only cookie; the
frontend must not store session tokens or passwords.

## Checks

```bash
npm test
npm run lint
npm run build
```

The Vite configuration uses SPA mode, so its production preview falls back to `index.html` for
unknown paths such as `/simulations/example`. Configure the production static host with the same
fallback; `BrowserRouter` routes cannot be refreshed directly otherwise.

Place API mapping tests beside modules in `src/api` and component tests beside the component.
