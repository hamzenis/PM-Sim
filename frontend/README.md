# PM-Sim frontend

The frontend is a React 19 application built with Vite and Chakra UI. It provides professor
workflows for scenarios, classes, students, results, and audit history, plus the student simulation
workflow.

## Requirements

- Node.js `^20.19.0 || ^22.13.0 || >=24.0.0`
- npm
- The PM-Sim backend at <http://127.0.0.1:8000>

## Run locally

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite (normally <http://localhost:5173>). The development server proxies
relative `/api` requests to the backend.

## Checks

```bash
npm run lint
npm test
npm run build
```

## Documentation

Use the [frontend documentation index](docs/README.md) for architecture, routing, API integration,
authentication, UI conventions, testing, accessibility, and deployment.
