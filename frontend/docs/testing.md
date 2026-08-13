# Frontend testing

Run checks from `frontend/`:

```bash
npm ci
npm ls --depth=0
npm run lint
npm test
npm run build
```

`npm test` uses `vitest run`, so it runs once and exits. Vite configures the `jsdom` environment,
global Vitest APIs, restored mocks, and `src/setupTests.js`, which installs Testing Library's
`jest-dom` matchers.

## Colocated Vitest and Testing Library tests

Put `Thing.test.jsx` beside `Thing.jsx`; put page tests beside pages and `*.test.js` API mapping tests
beside modules in `src/api/`. Test observable behavior rather than component internals. Query by the
same roles, names, labels, and text a user encounters (`getByRole`, `getByLabelText`, and
`findByRole`) instead of CSS classes or test IDs. Use `@testing-library/user-event` for realistic
typing, focus, and keyboard sequences, and await asynchronous rendering.

Render the minimum real providers a unit needs, such as `ChakraProvider`, `MemoryRouter`, and an auth
context value. Mock the network boundary or API module—not React internals—and reset mock state so
tests remain independent. Cover loading, success, useful empty, recoverable error, validation,
keyboard, and role-dependent paths when they exist.

## API mocking and mapping

API module tests such as `src/api/auth.test.js`, `src/api/classes.test.js`, and
`src/api/simulations.test.js` verify request method, path, serialized body, and transformation of
backend payloads into UI-facing values. Add or change this coverage whenever an endpoint, request
shape, response mapping, error mapping, or credentials behavior changes. Keep realistic fixtures
small and assert the contract rather than repeating implementation details.

In page/component tests, mock the relevant API exports and exercise loading and failure responses as
well as successful data. In Playwright, `tests/visual/pages.spec.js` intercepts `**/api/**` with fixed
fixtures so screenshots do not depend on a live backend. A missing fixture should not silently turn a
meaningful page into an empty response; add an explicit route fixture for new visual scenarios.

## Choosing the right coverage

- **Component coverage:** add a colocated test for reusable interaction, conditional presentation,
  validation, keyboard behavior, or a regression confined to a component. Existing dialog, form,
  feedback-state, and chart tests show these patterns.
- **Page coverage:** add a colocated page test for orchestration, route parameters, loading/error/empty
  states, or a workflow across multiple components. `src/pages/Login.test.jsx` and
  `src/pages/ScenarioOverview.test.jsx` are examples.
- **API-mapping coverage:** add a `src/api/*.test.js` case whenever a frontend/backend contract or
  payload-to-view-model transformation changes, even when a component test also exists.
- **Accessibility coverage:** extend `src/accessibility.test.jsx` when adding a materially distinct
  public, professor, or student structure, or a complex form, dialog, or chart. Also keep focused
  keyboard/name assertions beside the affected component. Axe does not replace manual review.
- **Visual coverage:** add a stable page state to `tests/visual/pages.spec.js` when layout, hierarchy,
  responsive behavior, theme usage, or a high-value role/route workflow could regress visually. A
  logic-only utility normally does not need a screenshot.

New routes need tests for every allowed role and a denied/redirected case for roles that cannot open
them. Update the Playwright role/route fixtures when a route is a high-value representative screen;
do not rely only on a happy-path screenshot to prove authorization.

## Stable dates, locale, and time

Use explicit ISO 8601 timestamps with a timezone and fixed current-time mocks when relative time is
under test. Do not construct assertions from the developer's current clock. Assert localized output
through shared formatters, and make the desired locale/timezone explicit. Playwright fixes `en-US`,
UTC, light color scheme, and reduced motion in `playwright.config.js`; Vitest inherits the process
timezone, so use `TZ=UTC npm test` to reproduce CI-like date behavior while repairing ambiguous tests.

## Accessibility checks

Run the axe coverage through `npm test`, but also make Testing Library assertions for semantic role,
accessible name, label/error association, focus movement, and keyboard behavior. Then complete the
manual checks in the [accessibility guide](accessibility.md). Automated axe results cannot verify
plain language, logical focus, correct alternative text, usable reflow, or whether an interaction is
understandable.

## Playwright visual tests

Install the pinned Chromium build once and compare screenshots:

```bash
npx playwright install chromium
npm run test:visual
```

The suite starts Vite on `127.0.0.1:4173`, intercepts API calls, waits for a named ready state and
fonts, disables animations and the caret, and captures desktop/mobile projects plus focused tablet
coverage. Keep fixtures deterministic and wait on user-visible readiness—not arbitrary timeouts.

### Reviewing visual diffs and snapshots

When a comparison fails:

1. Open the expected, actual, and diff artifacts in `test-results/` (or the HTML report in
   `playwright-report/`). Review the entire desktop and mobile page, not only the highlighted area.
2. Re-run the specific test to rule out missing fonts, browser availability, animation, or other
   environmental instability. Fix nondeterminism rather than increasing tolerances or masking a
   meaningful region.
3. Trace every changed pixel to the intended UI/code change. Check wrapping, clipping, focus,
   loading, fixture data, typography, and nearby layouts. An unexplained diff is a regression until
   understood.
4. Only after that review, update baselines with `npm run test:visual:update`. Inspect all changed PNGs
   under `tests/visual/__screenshots__/` and rerun `npm run test:visual`.
5. Commit legitimate baseline changes in the same commit as the UI change and describe the reason in
   review. Never update a snapshot solely to make CI green or broaden masking to hide a defect.

A baseline update is legitimate when an approved visual change intentionally alters layout, copy,
theme, responsive behavior, or stable fixture output, or when the pinned renderer/browser changes
and the resulting differences have been reviewed. It is not legitimate for intermittent timing,
local font differences, stale dependencies, an unavailable browser, an accidental API response, or
an unexplained shift.

Committed baselines in `tests/visual/__screenshots__/` are source-controlled review artifacts.
Generated `test-results/`, `playwright-report/`, `coverage/`, and `dist/` directories must not be
committed; they are ignored by the repository. Do not add ad hoc actual/diff screenshots elsewhere.

## Related documentation

- [Accessibility](accessibility.md)
- [UI guidelines](ui-guidelines.md)
- [Development troubleshooting](development.md#troubleshooting)
- [API integration](api-integration.md)
- [Backend testing](../../backend/docs/testing.md)
