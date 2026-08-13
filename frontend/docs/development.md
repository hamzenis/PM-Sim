# Frontend development

Run all commands in this guide from `frontend/` unless stated otherwise.

## Node.js and installation

The checked-in `.nvmrc` pins Node.js `22.13.0`, the recommended contributor and CI-compatible
version. `package.json` permits `^20.19.0`, `^22.13.0`, or `>=24.0.0`; older Node 20 and Node 22
releases are not supported by the Vite toolchain. With nvm:

```bash
nvm install
nvm use
node --version
npm ci
```

Use `npm ci`, not `npm install`, for a clean, reproducible install from `package-lock.json`. Run
`npm ls --depth=0` to diagnose an incomplete or invalid dependency tree.

## Environment configuration and the API proxy

Start the backend on `http://127.0.0.1:8000`, then start Vite. The default
`VITE_API_BASE_URL` is empty, so `src/api/client.js` sends relative `/api/...` requests. During
development, Vite proxies those requests to `http://127.0.0.1:8000`; the browser sees a same-origin
request and the backend URL is not embedded in application code.

For a backend on another origin, copy the template and set the complete origin:

```bash
cp .env.template .env
printf 'VITE_API_BASE_URL=https://api.example.test\n' > .env
```

Restart Vite after changing an environment file. `VITE_` values are exposed in the browser bundle,
so never put a password, token, or other secret in them. A separate API origin must allow the exact
frontend origin, credentialed CORS requests, and the session cookie attributes required by the
deployment. The API client always uses `credentials: 'include'`.

## Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server (normally port 5173). |
| `npm run build` | Create the production bundle in `dist/`. |
| `npm run lint` | Check all frontend JavaScript and JSX with ESLint. |
| `npm test` | Run the colocated Vitest suite once. |
| `npm run test:visual` | Compare Playwright screenshots with committed baselines. |
| `npm run test:visual:update` | Replace baselines after an intentional, reviewed UI change. |

See [frontend testing](testing.md) before updating screenshots.

## Source organization

- `src/Routing.jsx` inventories routes and public, authenticated, and professor-only gates.
- `src/pages/` contains route-level screens; `src/components/` contains reusable workflow UI.
- `src/components/SimulationV2/` and `src/components/ClassManagement/` contain their larger domains.
- `src/api/` owns HTTP calls and maps API payloads; `src/context/` owns shared React context.
- `src/utils/` owns shared presentation formatting, and `src/theme.js` owns Chakra tokens.
- `tests/visual/` contains Playwright fixtures and screenshots; `public/` contains static assets.

Keep component and page tests beside the file they exercise and API tests beside their API module.

## Linting and formatting

Run `npm run lint` before committing and fix the cause rather than adding blanket disable comments.
The repository has no standalone formatter script. Match the surrounding file: current source
generally uses tabs, single quotes, semicolons, and trailing commas, while configuration and docs may
use their established indentation. Let ESLint define enforceable syntax, and avoid formatting
unrelated code in a functional change.

## Troubleshooting

### Backend connection failures

Confirm the backend is listening at `127.0.0.1:8000`, request `/api/...` rather than the backend root,
and inspect both the Vite terminal and browser Network panel. If `VITE_API_BASE_URL` was set earlier,
remove it to restore the proxy or correct it and restart Vite. Do not mix `localhost` and `127.0.0.1`
when cookie or origin rules depend on an exact host.

### Cookie or CORS problems

Authentication uses an HTTP-only cookie, so it will not appear through JavaScript. Verify the login
response sets the cookie and later requests include it. For cross-origin development, the backend
must return a specific allowed origin (not `*`) with credential support, and cookie `SameSite`,
`Secure`, domain, and path settings must match the browser context. Prefer the Vite proxy locally.

### SPA deep-link 404s

Vite serves the application in SPA mode, but a production server must rewrite unknown, non-file
paths to `index.html`. Configure that fallback if refreshing `/classes` or `/simulations/run-1`
returns a server 404; do not rewrite `/api` or static asset requests.

### Unsupported Node versions

If Vite reports an engine or syntax error, run `node --version` and `npm version`, then `nvm use`.
The major version alone is insufficient: Node 20 must be at least 20.19 and Node 22 at least 22.13.

### Stale or broken dependencies

Remove only generated dependencies and reinstall from the lockfile:

```bash
rm -rf node_modules
npm ci
npm ls --depth=0
```

Do not delete or regenerate `package-lock.json` merely to fix a local cache problem.

### Test timezone differences

Prefer fixed ISO timestamps and explicit locale/timezone expectations. Playwright is pinned to
`en-US` and UTC, but Vitest inherits the process timezone; run `TZ=UTC npm test` when investigating a
local-only date failure and make the test's time assumptions explicit rather than weakening it.

### Playwright browser availability

Install the version pinned by the package lock with `npx playwright install chromium`. On a minimal
Linux environment, `npx playwright install --with-deps chromium` may also be necessary. A missing
browser is an environment failure, not a reason to update snapshots.

## Related documentation

- [UI guidelines](ui-guidelines.md)
- [Frontend testing](testing.md)
- [API integration](api-integration.md)
- [Frontend deployment](deployment.md)
