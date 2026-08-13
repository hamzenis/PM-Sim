# Full-system deployment

This guide describes releasing the FastAPI application in `backend/` and the compiled React
application in `frontend/dist/` as one service. It is an integration checklist, not a replacement
for the detailed [backend deployment guide](../backend/docs/deployment.md),
[SQLite operations guide](../backend/docs/sqlite-operations.md), or
[frontend development and build guide](../frontend/docs/development.md).

## Build-time and runtime configuration

The frontend configuration is compiled into its JavaScript. From `frontend/`, leave
`VITE_API_BASE_URL` empty for same-origin `/api/...` requests, or set it to the API origin (for
example, `https://api.pm-sim.example.edu`) before running `npm run build`. Rebuild to change it;
changing a server environment variable after the build does not alter files already in `dist/`.
Never put secrets in a `VITE_` value because users can inspect the bundle. Follow the
[frontend development and build guide](../frontend/docs/development.md) for supported Node versions,
dependency installation, and build commands.

The backend reads runtime configuration. Start from [`backend/.env.example`](../backend/.env.example)
and supply production values through the service manager rather than committing a `.env` file.
In particular, use an absolute durable `DATABASE_URL`, set `RELOAD=false`, set
`COOKIE_SECURE=true`, and select production values for the bind address, port, session lifetime,
SQLite behavior, and log level. The authoritative meanings and constraints are in the
[backend deployment guide](../backend/docs/deployment.md).

## Reference topologies

### Preferred: one browser origin

Expose one HTTPS origin, such as `https://pm-sim.example.edu`:

```text
browser --HTTPS--> reverse proxy
                    |-- /api/*, /health, /health/ready --> one private backend process
                    `-- / and static files             --> frontend/dist/
```

Terminate TLS at the reverse proxy, redirect HTTP to HTTPS, and do not expose the backend port to
the public network. Forward `/api` without stripping or duplicating that prefix. Pass the original
host, client address, and scheme using the proxy's conventional headers (for example `Host`,
`X-Forwarded-For`, and `X-Forwarded-Proto: https`), overwrite rather than trust inbound spoofed
values, and configure the application/proxy to trust forwarded headers only from known proxy
addresses. Preserve `Set-Cookie` headers. With `VITE_API_BASE_URL` empty, API requests and the
`HttpOnly`, `Secure`, `SameSite=Lax` session cookie remain same-origin and CORS is unnecessary.

### Separate frontend and API origins

An alternative layout uses, for example, `https://pm-sim.example.edu` for `frontend/dist/` and
`https://api.pm-sim.example.edu` for the backend. Build with
`VITE_API_BASE_URL=https://api.pm-sim.example.edu`, route `/api/*` (plus health endpoints if they are
intentionally exposed) at the API origin to the backend, and use HTTPS on both origins. Apply the
same private-upstream and trusted-proxy-header rules described above.

**The current backend has no CORS middleware or allowed-origin setting, so this topology does not
work without a reviewed backend change.** Before using it, implement and test an exact allowlist
for the frontend origin, credentialed requests and preflights. Responses must use that specific
origin, permit credentials, and vary by `Origin`; never combine cookies with
`Access-Control-Allow-Origin: *`. The frontend API client includes credentials. Confirm the
session-cookie `Domain`, `Path`, `Secure`, and `SameSite` attributes work for the selected sites;
cross-site (not merely cross-origin) hosting may require a different `SameSite` policy and the
corresponding CSRF protections. Do not weaken cookie or CORS policy just to make this topology pass.

## Static hosting and SPA routing

Serve the contents of `frontend/dist/`, with `index.html` as the entry point. Apply these routing
rules in order:

1. Proxy `/api` and every `/api/*` path to the backend; these paths must never receive the SPA.
2. Route `/health` and `/health/ready` to the backend (prefer restricting them to the load balancer
   or operations network).
3. Serve existing static files, including `/assets/*`, directly from `frontend/dist/`. A missing
   static asset must return `404`, not `index.html`.
4. For a `GET` or `HEAD` to any remaining frontend route with no matching file, return
   `frontend/dist/index.html` with `200`. This fallback is required for direct navigation and
   refreshes such as `/simulations/<run-id>` or `/scenarios`.

Do not cache `index.html` aggressively: use `no-cache` (or a similarly revalidating policy) so it
quickly points at the current bundle. Vite's content-hashed files under `/assets/` may be cached for
a long time with `immutable`. Avoid rewriting failed API or asset requests to HTML, which hides
deployment errors and causes misleading JSON or module parse failures.

## Release sequence

Prepare the previous application release, frontend bundle, database revision, and rollback commands
before starting. SQLite production uses one backend process; do not attempt a multi-worker rolling
deployment against the same database.

1. **Back up and record.** Drain writes or stop the old backend as required by the
   [SQLite operations guide](../backend/docs/sqlite-operations.md). Create and verify an off-host
   backup, and record the application commit and current Alembic revision.
2. **Stage and migrate.** Install the locked backend environment from the new release and run
   `alembic upgrade head` exactly once with production configuration. Do not let concurrent
   instances race migration.
3. **Roll out the backend.** Start one supervised new backend on its private interface. Keep public
   traffic closed until readiness and representative authenticated reads pass.
4. **Build and roll out the frontend.** Build from the intended frontend commit with the topology's
   `VITE_API_BASE_URL`. Publish `dist/` atomically (release directory/symlink or equivalent), so
   `index.html` and its hashed assets cannot be observed half-copied.
5. **Handle caches.** Ensure every new hashed asset is available before switching `index.html`.
   Revalidate or purge cached HTML and service/CDN error responses, but retain old hashed assets for
   at least the overlap window so already-open or cached pages continue to load.
6. **Smoke test and open traffic.** Run the readiness checks below through the same public proxy and
   hostname users will use. Monitor authentication failures, `4xx`/`5xx`, database locks, and asset
   errors while restoring traffic.
7. **Roll back if necessary.** For a frontend-only problem, atomically restore the previous
   `index.html`/bundle while retaining both releases' hashed assets. For backend code, drain traffic
   and restore the previous backend only if the migrated schema is compatible. For an incompatible
   migration, stop all writers and use a rehearsed safe downgrade or restore the verified backup;
   a restore loses post-backup writes. Re-run all smoke checks before reopening traffic.

## Readiness and smoke checks

Use a dedicated non-demo smoke user and a fresh cookie jar. Treat opaque IDs as values discovered
from responses, not stable constants. At minimum verify:

- **API readiness:** `GET /health/ready` returns `200` through the proxy and indicates database
  connectivity. Also check `GET /health` for process liveness.
- **Authentication:** `POST /api/auth/login` over HTTPS sets the expected secure session cookie;
  `GET /api/auth/me` with that cookie returns the smoke user. Verify logout invalidates it.
- **Scenario listing:** for the user's role, `GET /api/scenarios` (professor) or
  `GET /api/classes/available-scenarios` (student) returns a valid JSON list.
- **Run retrieval:** list `GET /api/simulations`, select an accessible run, then verify
  `GET /api/simulations/<run-id>` returns it. If the smoke account has no run, provision a known
  non-production fixture before the release rather than modifying classroom data during a check.
- **Static assets:** `GET /` returns HTML, each CSS/JavaScript URL referenced by that HTML returns
  `200` with the correct content type, and a deliberately missing `/assets/...` URL returns `404`
  rather than HTML.
- **Nested navigation:** in a new browser session, directly open an authenticated nested route such
  as `/simulations/<accessible-run-id>` (or `/scenarios`), confirm the server supplies the SPA and
  the application renders after authentication instead of returning a proxy `404`.

Readiness alone does not prove that migrations, cookies, routing, or scenario data are correct.

## Version overlap and compatibility

Deployments can temporarily combine an old open tab or cached `index.html` with the new API, and a
new frontend with the prior API during rollout or rollback. Each release must define and test that
overlap window. Prefer additive API and schema changes: keep existing endpoints and response fields,
make new response fields ignorable, make new request fields optional, and do not change identifier
meaning or cookie behavior in place. Deploy backend support before a frontend begins using it;
remove old API behavior only after the maximum HTML/asset cache and open-session window has passed.

If compatibility cannot be maintained, use a coordinated maintenance window that blocks traffic,
migrates the backend, and atomically publishes the matching frontend. Do not rely on deployment
order alone: retained tabs can still run an old bundle. Fail clearly on unsupported versions and
keep database migrations backward compatible through rollback where practical. Pin a simulation
run to its persisted scenario/revision semantics; a release must not reinterpret historical opaque
identifiers or stored runs merely to match a new UI.

## Production-security checklist

- [ ] No demo accounts or published demo credentials exist in production; real accounts follow the
      institution's provisioning and offboarding process.
- [ ] All browser traffic uses HTTPS (with HTTP redirected), TLS keys are protected, and session
      cookies are `Secure`, `HttpOnly`, and assigned a reviewed `SameSite`, domain, path, and lifetime.
- [ ] The database and its directory are owned by the service account with least-privilege
      permissions; the SQLite file and backend upstream are not publicly reachable.
- [ ] Secrets are supplied by an access-controlled secret/service manager, are absent from Git and
      `VITE_` variables, and have a rotation procedure.
- [ ] Central logs are access-controlled, rotated, and redacted: never log passwords, cookies,
      tokens, database credentials, or complete sensitive scenario/run payloads.
- [ ] Encrypted off-host backups run to a monitored schedule, integrity is checked, retention meets
      policy, and restoration is rehearsed.
- [ ] CORS, proxy trust, firewall rules, and exposed health/documentation endpoints are restricted to
      the minimum required surface.
- [ ] Opaque technical identifiers (user, class, scenario, revision, and run IDs) are treated as
      potentially sensitive: authorization is enforced on every lookup and IDs are removed from
      public URLs, screenshots, support bundles, analytics, and logs unless operationally necessary.
