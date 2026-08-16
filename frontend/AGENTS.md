# Frontend agent guide

This file applies to everything under `frontend/` and supplements the repository-root `AGENTS.md`.
The implementation and colocated tests are authoritative; the guides under `docs/` describe the
intended user experience and must remain synchronized with behavior.

## Read before editing

Start with `README.md` and `docs/README.md`, then choose the smallest relevant set:

- component ownership, providers, state flow, and route matrix: `docs/architecture.md`;
- Node requirements, local setup, environment variables, and troubleshooting: `docs/development.md`;
- route registration and role gates: `docs/routing.md`;
- HTTP client and endpoint adapters: `docs/api-integration.md`;
- session restoration, cookies, and authentication transitions: `docs/authentication.md`;
- theme, responsive layout, forms, dialogs, charts, and feedback states: `docs/ui-guidelines.md`;
- test placement, API mocks, accessibility checks, and visual baselines: `docs/testing.md`;
- keyboard, focus, semantics, contrast, motion, and chart alternatives: `docs/accessibility.md`;
- build-time settings and hosting requirements: `docs/deployment.md`.

Trace a workflow end to end before changing it: route gate -> page orchestration -> feature
component -> API adapter/context/utility -> colocated tests -> visual and user-facing documentation.

## Frontend architecture boundaries

- `src/pages` owns route-level orchestration, request state, and composition. Move reusable feature
  rendering into `src/components`; do not turn pages into a second transport layer.
- `src/components` owns reusable presentation and interaction. Components receive data and callbacks
  or call the established domain adapter; they must not duplicate endpoint paths or response mapping.
- `src/api/client.js` is the only low-level HTTP boundary. Domain modules in `src/api` own endpoint
  paths, request serialization, response-to-view-model mapping, and adjacent contract tests.
  Components and pages must not call `fetch` directly.
- `src/context` is reserved for genuinely cross-tree application state. Keep page-local and
  feature-local state close to its owner rather than expanding a global context by default.
- `src/utils` contains pure, reusable transformations. Keep locale-aware dates, money, percentages,
  scores, and status labels in the shared presentation utilities instead of reimplementing them.
- `src/Routing.jsx` is the route-policy owner. Frontend gates improve navigation but never replace
  backend authorization. Register every new route inside the correct public, authenticated, or
  professor-only branch and update the documented route matrix.
- `src/theme.js` owns shared visual tokens. Prefer Chakra primitives, semantic tokens, and responsive
  props over raw colors, one-off CSS, fixed dimensions, or a parallel component system.

## Implementation and security conventions

- Use function components and hooks, follow the configured ESLint rules, and match neighboring JSX
  style. Keep render logic declarative and effects narrow, cancellable where needed, and dependency
  complete. Do not suppress hook or lint rules to hide an ownership problem.
- Model each request-driven region explicitly: loading, success, useful empty, and recoverable error.
  Prevent stale or out-of-order responses from replacing newer state, and preserve user input after
  recoverable failures.
- Treat backend payloads as an external contract. Normalize them once in the relevant API adapter,
  retain machine values for logic, and expose plain-language labels only at the presentation edge.
- Authentication uses an HTTP-only cookie. Keep `credentials` behavior centralized, never read or
  persist tokens, and never place passwords, session material, private scenario answers, or personal
  student data in logs, browser storage, URLs, screenshots, fixtures, or rendered diagnostics.
- Keep role and ownership decisions authoritative on the backend. Do not infer access from hidden
  controls, guessed identifiers, or client state; handle `401`, `403`, `404`, and conflicts using the
  established normalized error behavior without leaking restricted data.
- Keep identifiers as route/request/list keys, not ordinary UI copy. Display scenario names, class
  names, usernames, revisions, and other human-readable values through shared formatting patterns.
- Avoid adding dependencies for behavior already supplied by React, Chakra, the browser, or a small
  local helper. Intentional dependency changes require `package.json` and `package-lock.json` to move
  together and must be installed with the supported Node version and lockfile workflow.

## Accessibility and responsive UI

Accessibility is a functional requirement for every UI change. Prefer native semantics before ARIA,
give each page one descriptive `h1`, label every control, preserve a visible focus indicator, and
support the native keyboard interaction model. Use `ConfirmDialog` for destructive actions with
initial focus on the safe action and focus restoration on close.

Use the established responsive page container and test narrow and wide layouts. Interactive targets
must remain at least 44 by 44 CSS pixels, content must reflow without ordinary two-dimensional page
scrolling, and meaning must not depend on color, position, or motion alone. Every chart needs the
same values in an accessible table, readable units, a visible legend, and non-color series cues.

For a perceptible change, manually review desktop and mobile rendering, keyboard and focus order,
loading/error/empty states, zoom/reflow, contrast, and reduced motion. Capture and inspect a
screenshot when required by the root guide; screenshots must contain only deterministic fictional
data.

## Tests and required checks

Colocate Vitest/Testing Library tests with the source they exercise. Test observable behavior using
roles, names, labels, and realistic user events rather than implementation details, CSS selectors,
or test IDs. Mock the API boundary—not React internals—and cover the relevant loading, success,
empty, validation, error, keyboard, and role-dependent paths.

Add or update:

- `src/api/*.test.js` for endpoint paths, methods, payloads, response mapping, or normalized errors;
- page tests for orchestration, route parameters, role behavior, and request-state transitions;
- component tests for reusable interactions, dialogs, forms, charts, and regressions;
- `src/accessibility.test.jsx` for materially new page structures or complex interactions;
- `tests/visual/pages.spec.js` and its deterministic fixtures for meaningful layout, theme,
  responsive, or high-value workflow changes.

From `frontend/`, iterate with the smallest focused test and finish an affected frontend change with:

```bash
npm ci
npm ls --depth=0
npm run lint
npm test
npm run build
npm run test:visual
```

Install the lockfile-pinned Chromium build with `npx playwright install chromium` when it is not
already available. Never update snapshots merely to clear a failure: inspect expected, actual, and
diff images; account for every changed pixel; update with `npm run test:visual:update` only for an
intentional reviewed visual change; then rerun the visual suite. Do not commit `dist/`, `coverage/`,
`test-results/`, `playwright-report/`, or ad hoc screenshots.

From the repository root, also run:

```bash
uv run --project backend python scripts/check_docs.py
```

## Change-coupling checklist

- Route or role-gate change: update `src/Routing.jsx`, allowed and denied-role tests,
  `docs/architecture.md`, and `docs/routing.md`.
- Endpoint, payload, status, or error change: update the domain adapter and its tests, affected
  request states, `docs/api-integration.md`, and the backend route/model/tests and `docs/api.md`.
- Session or credential change: update client/provider tests, `docs/authentication.md`, and the
  backend authentication/CORS/cookie contract.
- Shared UI, theme, form, dialog, chart, or formatting change: update focused tests,
  `docs/ui-guidelines.md`, accessibility coverage, and reviewed visual baselines when pixels change.
- Build, environment, proxy, or hosting change: update `docs/development.md`, `docs/deployment.md`,
  and CI or root operations documentation where applicable.
- New dependency: justify its ownership and maintenance cost, update both package files, and verify
  clean installation, lint, tests, build, and affected browser behavior.

Before handoff, inspect the complete diff for accidental secrets or personal data, raw internal
identifiers, inaccessible interactions, unhandled request states, stale API mappings, nondeterministic
fixtures, unexplained snapshot changes, generated output, and documentation drift.
