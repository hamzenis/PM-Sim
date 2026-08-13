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

Use the [frontend documentation index](docs/README.md) for local development, architecture, routing,
API integration, authentication, UI guidelines, testing, accessibility, and deployment. In
particular, follow the [UI guide](docs/ui-guidelines.md#adding-a-page-consistently) when adding a page.

Visual snapshots are review artifacts: never update them only to make CI pass. Follow the
[visual-diff and baseline procedure](docs/testing.md#reviewing-visual-diffs-and-snapshots) for every
snapshot change.
