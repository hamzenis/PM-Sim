# Backend deployment

This is the production baseline for the current SQLite deployment. Development-only demo commands
and credentials are explicitly excluded.

## Process topology and reverse proxy

Run one supervised Uvicorn process with one worker, using `uv run python main.py serve` from a stable
`backend/` release directory. With SQLite there must be no second worker, host, or overlapping
application instance. A service manager should provide environment variables, restart on failure,
set resource limits, and stop gracefully. Do not enable `RELOAD` or pass `--reload` in production.

Place a reverse proxy in front of Uvicorn. It should terminate HTTPS, expose only intended routes,
forward the original host/scheme safely, impose request/body/time limits suitable for scenario JSON,
and send `/api`, `/health`, and `/health/ready` to the backend. Bind Uvicorn to loopback or a private
interface; firewall its upstream port. Configure proxy trust only for known proxy addresses.

The backend currently installs no CORS middleware and exposes no allowed-origins setting. Serve the
frontend and API under one browser origin (for example `https://pm-sim.example.edu/` and `/api`). A
separate frontend origin requires a code change adding a strict origin allowlist and credentialed
preflight tests. Never use `Access-Control-Allow-Origin: *` with authentication cookies.

## HTTPS, cookies, and accounts

Redirect HTTP to HTTPS at the proxy and set `COOKIE_SECURE=true`. The session cookie is also
`HttpOnly` and `SameSite=Lax`; ensure the proxy does not rewrite it incorrectly and that browser
requests include credentials. Keep hostnames and clocks stable, protect TLS keys, and use current
institutional TLS policy.

Create real professor accounts interactively with `uv run python main.py create-professor`; keep terminal access and logs
restricted. **Never run `create-demo` in production.** Its published credentials
`professor` / `professor-password` and `student` / `student-password` are development-only and must
be treated as compromised everywhere.

## Database and release startup

Use an absolute `DATABASE_URL` to a restricted, durable local filesystem outside the code/release
directory. Backups must be outside both the database and release directories and copied off-host.
Follow [SQLite classroom operations](sqlite-operations.md) for modes, WAL, space, and recovery.

Do not allow every prospective process to race automatic migrations. A release procedure should:

1. Drain/stop the single application and verify the database has no other users.
2. Back up and verify using the old release with
   `uv run python main.py backup --output /srv/pm-sim-backups`; record commit and Alembic revision.
   `backup` deliberately never migrates, so this is a rollback image of the current schema.
3. Install the locked environment with `uv sync --frozen` and run all checks in CI.
4. Run `uv run python main.py migrate` once from the new release with production environment
   values.
5. Start one process with `uv run python main.py serve --no-migrate`. This makes migration
   ownership explicit and prevents startup from mutating the verified schema. For simple local
   operation, `serve` without that option still migrates before starting.
6. Gate traffic on readiness and a smoke test, then monitor errors and lock behavior.

The command-specific `--no-migrate` option exists only on `serve` and database-mutating
administration commands. Use it only after a successful explicit migration or for controlled
diagnostics, never to run a mismatched release. `backup`, `batch`, and `migrate` do not accept it:
backup and batch never migrate, while bypassing the sole purpose of `migrate` is meaningless.

## Health checks and logs

`GET /health` is a liveness check for the Python process. `GET /health/ready` executes `SELECT 1`
and returns `503` if the database is unavailable. Probe liveness sparingly and readiness before
routing traffic. Neither endpoint proves migrations are at head, data is semantically valid, or a
simulation can replay; deployment smoke tests must cover those separately.

Collect stdout/stderr through the service manager into centralized, access-controlled logs. Include
UTC timestamps, release/commit, host, restart reason, proxy request ID, status, latency, and Alembic
job output where supported. Do not log passwords, cookies, authorization tokens, full sensitive
scenario/state payloads, or database URLs containing credentials. Use `LOG_LEVEL=info` normally,
rotate/retain logs under policy, monitor `5xx`, `409` trends, auth failures, database locks, readiness,
disk/WAL growth, and backup results.

## Scheduled operations

Schedule `python main.py cleanup-sessions` at least daily according to session volume. Schedule
`python main.py backup --output /srv/pm-sim-backups` to meet
the recovery-point objective, serialize it with release/restore operations, verify SQLite integrity
and foreign keys, checksum/encrypt it, and copy off-host. Monitor the scheduler itself and regularly
restore into an isolated environment. `backup` never upgrades the database. `cleanup-sessions`
migrates by default and should use `--no-migrate` when an explicit release migration owns the
schema. See the SQLite guide for example retention and validation.

## Rollback

Prepare rollback before migration. Preserve the previous release/environment, verified
pre-migration backup, revision/commit metadata, and commands. If only application code fails and the
schema is backward compatible, drain traffic and restart the previous release. If schema/data has
changed incompatibly, stop all writers and either execute a previously tested safe Alembic downgrade
or restore the pre-migration backup; never improvise a downgrade that loses data. Validate integrity,
revision, readiness, authentication, representative scenario/run reads, and replay before reopening.

Restoring a backup discards writes made since it was taken. Record that decision, preserve forensic
copies, communicate the recovery point, and reconcile affected classroom activity. Do not attempt a
SQLite-to-PostgreSQL switch as an incident-time rollback; complete the readiness checklist in the
development guide first.

## Production checklist

- `RELOAD=false`, `COOKIE_SECURE=true`, non-debug `LOG_LEVEL`, one worker, private backend bind.
- Same-origin HTTPS proxy; no wildcard CORS; verified cookie login/logout behavior.
- Absolute local SQLite path, restricted account/directory, WAL space monitored.
- Exactly one migration owner; verified backup and rehearsed rollback for each release.
- Liveness, readiness, semantic smoke test, centralized redacted logs, backup/cleanup schedules.
- No demo users, credentials, or development-only commands against production data.

## Related documentation

- [Development and configuration](development.md)
- [SQLite classroom operations](sqlite-operations.md)
