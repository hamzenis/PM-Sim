# PM-Sim frontend

The frontend is a React 19 application built with Vite and Chakra UI. It provides professor
workflows for scenarios, classes, students, results, and audit history, plus the complete student
simulation workflow.

The installed toolchain uses React 19.2.8, Vite 8.2.1, Vitest 4.1.10 for tests, and ESLint 10.8.1
for code checks.

## Requirements

- Node.js `^20.19.0 || ^22.13.0 || >=24.0.0` (Node 22.13 or newer in the Node 22 LTS line is a
  good default; run `nvm use` if you use nvm)
- npm
- the PM-Sim backend running on `http://127.0.0.1:8000`

## Setup

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite (normally <http://localhost:5173>). The development server proxies
relative `/api` requests to `http://127.0.0.1:8000`, so no frontend environment variable is needed
for the standard local setup.

For a backend on a separate origin, copy `.env.template` to `.env` and set the complete API origin:

```bash
VITE_API_BASE_URL=https://api.example.test
```

Restart `npm run dev` after changing `.env`. The backend must explicitly allow the frontend origin
and credentialed requests when the applications are not served from the same origin.

## Application routes

- `/login`: authentication.
- `/scenarios`: professor scenario lifecycle or student assignments and runs.
- `/simulations/:run_id`: weekly student decisions, history, and final result.
- `/classes`: professor class, student, assignment, and result management.
- `/classes/:class_id/results/:run_id`: professor run audit.
- `/audit`: professor administrative history.
- `/change-password`: authenticated password change.

All HTTP requests go through `src/api/client.js`. Authentication uses an HTTP-only cookie, which
JavaScript cannot read; the browser sends it with API requests. The frontend must not store session
tokens or passwords. In production, serve the frontend and API from compatible origins and use
HTTPS so the browser's cookie and CORS policies permit these credentialed requests.

## Commands

```bash
npm run dev   # start Vite's development server
npm run lint
npm test      # run the Vitest suite once
npm run build
```

`npm run build` creates the production files in `dist/`. Vite handles fallback routing during
development, but the production web server or static host must rewrite unknown non-file paths to
`index.html`. Without this SPA deep-link fallback, refreshing a route such as
`/simulations/example` returns a 404.

Place API mapping tests beside modules in `src/api` and component tests beside the component.
