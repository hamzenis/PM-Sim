# React 19 final migration report

## Sign-off and scope

Final technical sign-off was performed independently on 2026-08-12 from the current branch, using Node.js `20.20.2`, npm `11.4.2`, Python `3.13.13`, and uv `0.7.22`. The audit covered every tracked file under the active `frontend/`, the Vite and CI configuration, frontend-facing FastAPI authentication/API/configuration code, backend tests, and the deployment documentation. Direct browser checks used Chromium 140 through Playwright against the real Vite proxy and a fresh FastAPI demo database.

The deprecated `frontend_depracated/` and `backend_deprecated/` applications are historical, non-deployed trees and are not part of the React 19 runtime. Their legacy dependencies and APIs must not be interpreted as active-application findings.

## Original environment

Commit `113b362` is the implementation baseline. Its manifest declared React and React DOM `^18.0.0`, Create React App / `react-scripts` `5.0.1`, Chakra UI `^1.8.8`, Emotion React `^11.9.0`, Emotion Styled `^11.8.1`, Framer Motion `^6.3.2`, React Router DOM `^6.3.0`, React Testing Library `^13.1.1`, user-event `^13.5.0`, and TypeScript `4.5.4` with React 18 typings. It had no standalone Vite, Vitest, jsdom, or ESLint version.

The baseline clean install was already broken: `npm ci` rejected the out-of-sync manifest/lockfile and exposed React 17-only transitive peer ranges. Because installation failed, CRA tests/build could not run; there was no lint script. These are baseline limitations, not final migration failures.

## Final environment (exact resolved versions)

Versions below are the installed results after a successful `npm ci`, not merely manifest ranges.

| Requested component | Final package | Exact version |
| --- | --- | --- |
| React | `react` | `19.2.8` |
| React DOM | `react-dom` | `19.2.8` |
| Vite | `vite` | `8.2.1` |
| React plugin | `@vitejs/plugin-react` | `6.0.5` |
| Chakra UI | `@chakra-ui/react` | `2.8.2` |
| Emotion | `@emotion/react` / `@emotion/styled` | `11.14.0` / `11.14.1` |
| Framer Motion | `framer-motion` | `11.18.2` |
| React Router | `react-router-dom` (and `react-router`) | `6.3.0` |
| React Testing Library | `@testing-library/react` | `16.3.2` |
| user-event | `@testing-library/user-event` | `14.6.4` |
| Vitest | `vitest` | `4.1.10` |
| jsdom | `jsdom` | `26.1.0` |
| ESLint | `eslint` | `10.8.1` |

Related resolved tools are Testing Library DOM `10.4.1`, jest-dom `6.9.1`, ESLint JS `10.0.1`, and React Hooks ESLint plugin `7.1.1`.

## Files changed by the migration

Relative to `113b362`, the migration:

* changed the frontend manifest and lockfile; environment template, manifest metadata, frontend documentation, this report, and root documentation;
* replaced CRA's `public/index.html` with root `index.html`, added `.nvmrc`, `vite.config.js`, and flat `eslint.config.js`;
* added the unified application-test workflow and removed the superseded migration-only workflow;
* changed API client/session-expiry integration and its API mapping tests;
* adjusted Navbar and Simulation V2 behavior and tests, added focused Navbar/confirmation-dialog tests, and updated component tests for current Testing Library/user-event behavior;
* removed unused `UserContext` and `customHooks` modules; and
* in final sign-off, changed `Routing.jsx` to render nothing during session restoration instead of mounting an empty `<Routes>`. This removes React Router's repeated `No routes matched location` console warning without changing the existing loading UI.

No backend API contract or database schema was changed for the React migration.

## React compatibility, dependency decisions, and reasons

* The entry point uses React 19's supported `createRoot` client API. No legacy render or hydration API remains.
* Create React App was replaced by Vite because CRA is obsolete and retained a stale dependency graph. Environment access moved from `process.env.REACT_APP_*` to `import.meta.env.VITE_API_BASE_URL`; Vite proxies `/api` in development and builds an SPA bundle.
* Chakra UI 2 was selected because it supports React `>=18` while preserving the existing component API. Chakra 3 would require an unrelated UI rewrite.
* Framer Motion 11 explicitly accepts React 18 or 19. Emotion 11 remains Chakra-compatible.
* React Testing Library 16 accepts React 19 and requires Testing Library DOM 10. user-event 14 tests use its asynchronous setup/API.
* Vitest/jsdom replace CRA/Jest test orchestration; ESLint's flat configuration replaces CRA's embedded lint setup.
* The unused TypeScript compiler and React type packages were removed because this is JavaScript/JSX with no `tsconfig`; keeping React 18 typings would be misleading.
* Router 6 is deliberately retained to avoid a Router 7 application rewrite. See the security finding below.

## Breaking changes addressed and source audit

The active frontend uses `createRoot`, modern context, and object/function refs. Searches of active source, configuration, and documentation found no runtime use of `react-scripts`, `ReactDOM.render`, `ReactDOM.hydrate`, `hydrateRoot`, `findDOMNode`, string refs, `contextTypes`/`childContextTypes`, `UNSAFE_*` lifecycle APIs, `process.env.REACT_APP_*`, or migration-added `eslint-disable` comments.

References to `react-scripts` and React 18 in this report are intentional baseline history, not active instructions. The deprecated application tree still contains legacy code by design and is outside deployment scope. No stale React 18 claim remains in active README documentation.

The final browser audit initially found a Router warning while authentication restoration temporarily supplied no routes. The narrow `isAuthenticating` return in `Routing.jsx` fixes that genuine runtime regression. After the fix, authenticated navigation and refresh produced no unexpected React/Router console warning or page error. The expected anonymous `/api/auth/me` response is HTTP 401 and appears as a browser failed-resource console entry; it is the designed session probe, not a React error.

## Dependency-tree and lockfile validation

After `npm ci`, `npm ls --depth=0` listed every manifest dependency exactly once and reported no `invalid`, `extraneous`, missing, or unmet direct dependency. A lockfile inspection found exactly one package node for React (`19.2.8`) and one for React DOM (`19.2.8`); the full `npm ls react react-dom --all` tree deduplicated all consumers to those versions.

`npm audit` did **not** pass cleanly: it reports two moderate advisories in `react-router@6.3.0` through `react-router-dom@6.3.0` concerning untrusted-path external redirects/backslash bypasses. This version was already declared in the React 18 baseline, so it is a remaining pre-existing dependency issue rather than a React 19 regression. It must nevertheless be resolved or explicitly risk-accepted before production approval.

## Validation results

| Check | Result |
| --- | --- |
| Clean install | Passed: 407 packages installed; audit still reports the two Router advisories. |
| Direct dependency tree | Passed: no invalid/extraneous direct dependencies. |
| Lint | Passed. |
| Frontend automated tests | Passed: 22 files, 58 tests. Coverage includes API credential/JSON/error behavior, forms, dialogs, menus/Navbar behavior, loading/error state, professor components, and simulation state/decision updates. |
| Production build | Passed: 1,115 modules transformed. Vite emitted a non-fatal 675.62 kB main-chunk advisory. |
| Backend format/lint | Passed: 109 files formatted and all Ruff checks passed. |
| Backend automated tests | Passed: 144 tests, with one pre-existing Starlette TestClient deprecation warning. |
| Browser startup and initial render | Passed in real Chromium against Vite/FastAPI. |
| Public routes | Passed for landing/login and `/gdpr`; anonymous protected paths redirect to login. |
| Authentication/session | Passed for professor and student login, cookie-backed session restoration after refresh, and logout. |
| Authorization | Passed: professor `/classes` renders with API data, role-gated navigation is present, and a student cannot access the professor class UI. |
| API calls and states | Passed through browser reads plus unit/integration suites; expected anonymous session probe returns 401. |
| Forms, dialogs, and menus | Passed through focused component tests and browser login/Navbar interaction. |
| Simulation updates | Passed through Simulation V2 frontend tests and backend turn/content/concurrency integration tests. |
| Browser console | Passed after the sign-off fix: no unexpected React/Router warnings, uncaught page errors, or authenticated failed requests. |
| Deep-link/deployment behavior | Vite development and production preview SPA fallback passed for direct route requests. Production infrastructure still must supply the documented rewrite to `index.html`; this repository does not define a concrete production web server. |

## Remaining issues

### Pre-existing issues

1. **Production blocker unless remediated or formally accepted:** two moderate React Router security advisories from retained Router 6.3.0.
2. The backend suite emits a Starlette TestClient deprecation warning recommending `httpx2`; it does not fail tests and is unrelated to React.
3. The old baseline could not clean-install and therefore has no trustworthy passing baseline test/build record.

### Migration-related issues

No known functional React 19 migration regression remains after suppressing the authentication-time empty-route warning. The migration toolchain, clean dependency graph, automated suites, build, API integration, and browser flows pass.

### Optional future improvements

* Split the 675.62 kB main JavaScript chunk for load performance.
* Add a committed Playwright/Cypress end-to-end suite so browser checks run continuously rather than only at sign-off.
* Add a production-server integration test once the actual hosting platform is selected.

## Recommendations and student handover

### Recommended

* Upgrade React Router within a reviewed compatible path that fixes both audit advisories, rerun the complete validation matrix, and only then issue unconditional production approval. If upgrade is deferred, record a security-owner risk acceptance and ensure application navigation targets cannot be influenced by untrusted paths.
* Keep React and React DOM pinned to the same exact version and update them together.
* Deploy `dist/` behind HTTPS, route `/api` consistently, set secure cookie/CORS policy for the chosen origins, and configure every unknown non-asset request to return `index.html`.
* Use the CI-equivalent commands (`npm ci`, dependency tree, lint, tests, build, backend Ruff/pytest) before merging.

### Optional

* Introduce route-level lazy loading/code splitting.
* Automate the professor/student browser smoke and console assertions.
* Add an explicit loading indicator during session restoration; final sign-off preserves the prior blank-loading behavior to avoid unrelated UI change.

### Advanced / not currently necessary

* Chakra UI 3, React Router 7, Server Components, SSR/hydration, TypeScript adoption, and React Compiler adoption are not required for React 19 compatibility. Each would be a separate project with its own design and validation plan.

For handover, students should use Node versions allowed by `package.json`, run `npm ci` rather than `npm install`, start FastAPI first and Vite second, use the Vite `VITE_API_BASE_URL` variable only for a separate API origin, and never restore CRA variables or `react-scripts`. Authentication is an HTTP-only session cookie; do not add tokens to local storage. New UI/API work should include Vitest/Testing Library coverage and preserve browser console cleanliness.

## Final conclusion

**The React 19 migration itself is technically complete and compatible, but the repository is not unconditionally ready for production sign-off.** The sole code/dependency condition preventing an unconditional production conclusion is the unresolved pair of moderate React Router audit advisories, unless the responsible security owner explicitly accepts that risk. A deployment must also implement and verify the documented SPA deep-link rewrite, HTTPS/API routing, and secure-cookie configuration in the real hosting environment; those infrastructure-specific checks cannot be proven by this source repository alone. No remaining React 19 runtime regression was found.
