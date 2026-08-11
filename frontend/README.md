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
npm start
```

Open <http://127.0.0.1:3000>. Create React App proxies relative API requests to the backend.

For a separate API origin, copy `.env.template` to `.env` and set:

```bash
REACT_APP_API_BASE_URL=https://api.example.test
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

The simulation screen derives its counters and task, budget, motivation, stress, and familiarity
graphs from the current run state and the player-visible state snapshots returned for completed
turns. Chart components are implemented with accessible SVG and do not require a charting
dependency.

## Checks

```bash
CI=true npm test -- --runInBand
npm run build
```

Place API mapping tests beside modules in `src/api` and component tests beside the component.
