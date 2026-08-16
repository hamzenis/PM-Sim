# Development and local operation

This guide covers the backend developer workflow, configuration, launcher, and migrations. Run all
commands from `backend/` unless a command says otherwise. Operational deployment belongs in
[deployment.md](deployment.md); SQLite recovery belongs in
[sqlite-operations.md](sqlite-operations.md).

## Repository orientation

- `app/main.py` assembles the FastAPI application and health endpoints; `main.py` is the operator
  launcher.
- `app/api/` contains HTTP adapters. Domain services live in `app/auth/`, `app/classes/`,
  `app/scenarios/`, `app/simulations/`, and `app/results/`.
- `app/simulation/` is the deterministic engine; `app/authored_content/` resolves and replays
  authored events; `app/db/` owns models, engines, sessions, and backups.
- `alembic/env.py` binds Alembic to application metadata and the configured database;
  `alembic/versions/` is the immutable, linear schema history.
- `tests/` mirrors domains in focused `test_*.py` modules. `scenario_examples/` contains versioned
  input examples, not test scratch data. `docs/` contains maintainer and operator guidance.
- `pyproject.toml` is the dependency/tool configuration and `uv.lock` is the reproducible lockfile.

## Python 3.13 and `uv`

The supported interpreter range is Python `>=3.13,<3.14`. The preferred workflow uses
[`uv`](https://docs.astral.sh/uv/) and installs the locked development dependency group:

```bash
uv python install 3.13
uv sync --frozen
uv run python main.py --help
```

Use `uv sync` (without `--frozen`) only when intentionally resolving dependency changes, review
the resulting `uv.lock` diff, and commit it with `pyproject.toml`. Prefix commands with `uv run` so
they use the project environment without relying on shell activation.

A conventional environment remains supported when `uv` is unavailable:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

On Windows PowerShell, activation is `.venv\Scripts\Activate.ps1`. Do not commit `.venv`.

## IDE expectations

Point the IDE at `backend/.venv`'s Python 3.13 interpreter (created by `uv sync`), set
`backend/` as the working directory/content root, and enable pytest discovery under `tests/`.
Configure Ruff as the formatter and linter with format-on-save and import organization enabled;
the repository's `pyproject.toml` is authoritative (`100` columns, Python 3.13). Do not let an IDE
silently use a repository-root interpreter, run `create_all()`, rewrite migrations, or reformat
JSON scenario examples.

## First local run

```bash
uv sync --frozen
uv run python main.py create-professor --username your-name
uv run python main.py serve --reload
```

The launcher migrates before database commands unless their command-specific `--no-migrate` is
supplied. The in-memory `batch` command never migrates. The default SQLite
file is `backend/pm_sim.db` because the URL is relative to the process working directory.

> **Development only:** `uv run python main.py create-demo` creates the fixed credentials
> `professor` / `professor-password` and `student` / `student-password`. Never run it against a
> production database and never expose those accounts outside an isolated local environment.

## Complete configuration reference

Settings are read once, at import/process startup. `.env.example` is documentation only: the
application does **not** load dotenv files. Export variables in the shell or inject them with the
service manager. Boolean values accept (case-insensitively, with surrounding whitespace ignored)
`1`, `true`, `yes`, `on` or `0`, `false`, `no`, `off`; other boolean text is rejected.

| Variable | Default | Accepted format and validation | Security/operational implication | Development / production recommendation |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./pm_sim.db` | Non-empty SQLAlchemy URL. A relative SQLite URL resolves from the working directory. | Selects all persistent user, auth, and simulation data. Credentials embedded in a URL may leak via process configuration or logs. | Dev: default or an isolated file. Prod: absolute local SQLite path with restricted permissions; do **not** switch to PostgreSQL until the readiness checklist below passes. Supply secrets through the process manager. |
| `HOST` | `127.0.0.1` | Non-empty bind address/hostname. | `0.0.0.0` or `::` exposes the port on available interfaces. | Dev: loopback. Prod: loopback behind a same-host proxy, or a private interface protected by firewall rules. |
| `PORT` | `8000` | Base-10 integer from `1` through `65535`. | A listening port can expose the API directly. | Dev: `8000`. Prod: a private upstream port selected by the service manager/proxy. |
| `RELOAD` | `false` | Boolean tokens listed above. | Reload watches files, restarts the process, and is unsuitable for stable service operation. | Dev: optional `true` or prefer CLI `--reload`. Prod: always `false`. |
| `COOKIE_SECURE` | `false` | Boolean tokens listed above. | Controls the session cookie's `Secure` attribute; false permits transmission over HTTP. Cookies remain `HttpOnly` and `SameSite=Lax`. | Dev: `false` only for local HTTP. Prod: `true`, with browser-facing HTTPS. |
| `SESSION_LIFETIME_HOURS` | `8` | Integer `>=1`. | Longer sessions increase the window for a stolen cookie; shorter sessions increase reauthentication. Existing records retain their stored expiry. | Dev: `8`. Prod: choose the shortest classroom-usable policy and schedule expired-session cleanup. |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | Integer `>=0`; ignored by non-SQLite engines. | Waits for transient locks rather than failing immediately; a large value can hide contention and delay requests. | Dev: `5000`. Prod SQLite: begin at `5000`, monitor lock waits, fix long transactions rather than continually increasing it. |
| `SQLITE_WAL` | `true` | Boolean tokens listed above; ignored for non-SQLite and in-memory SQLite. | WAL improves reader/writer concurrency but creates `-wal`/`-shm` companions and requires a reliable local filesystem. | Dev/prod SQLite: `true`; turn off only for a tested filesystem constraint, never to mask locking problems. |
| `LOG_LEVEL` | `info` | Case-insensitive `critical`, `error`, `warning`, `info`, `debug`, or `trace`. | Debug/trace may expose request context through library logs and greatly increase volume. | Dev: `debug` when needed. Prod: `info` or `warning`; restrict log access and retention. |

There is currently **no** environment variable for allowed frontend origins and no CORS middleware.
Use a same-origin reverse proxy in production. A separately hosted frontend will fail browser CORS
checks until an explicit, narrowly allowlisted CORS configuration is implemented and tested; do
not solve this with a wildcard origin when cookies are involved.

Invalid settings raise `ValueError` before the server starts. Reproduce with `uv run python -c
'from app.config import settings; print(settings)'`, inspect the named value, and remember that
changing the parent shell after startup does not reconfigure the running process.

## Launcher command reference

`uv run python main.py [command] [options]` defaults to `serve` for compatibility. Database commands
apply `alembic upgrade head` first. Their local `--no-migrate` bypasses that step only for controlled
diagnosis; `batch` is purely in memory and has no such option.

| Command | Purpose and behavior | Relevant options / cautions |
| --- | --- | --- |
| `serve` (default) | Migrates, then starts `app.main:app` through Uvicorn with exactly one worker. | `--host` and `--port` override environment values. `--reload` or `RELOAD=true` enables file watching and process restarts. Reload is **development only**. SQLite must remain single-worker. |
| `create-professor` | Prompts twice for a password and inserts a professor account; mismatch, invalid username/password, or duplicate credentials exits `2`. | `--username NAME` avoids the username prompt, but the password is deliberately not a CLI argument. Appropriate for production account provisioning when run through an audited terminal. |
| `create-demo` | Creates a demo professor, student, class, published scenario, and assignment. | `--scenario PATH` defaults to `scenario_examples/basic_project.json`. **Development only:** fixed printed passwords are public and the command can fail/partially conflict if rerun. Never use on production data. |
| `cleanup-sessions` | Deletes authentication sessions whose expiry is at or before current UTC and prints the count. | Safe to schedule; it does not revoke active sessions. Back up and monitor scheduled jobs. |
| `backup` | Uses SQLite's online backup API to make a timestamped `pm_sim-*.db` file. | `--output DIR` defaults to `backups`. File-based SQLite only; it refuses memory and PostgreSQL URLs. The destination must not already exist. Verify and copy off-host as described in the SQLite guide. |
| `batch` | Runs a scenario repeatedly through the in-memory simulation engine and prints a JSON report. | Positional `SCENARIO`; select `--strategy`, `--repetitions`, `--initial-seed`, and optionally `--employee-type`. It neither accesses nor migrates the database. |

Examples:

```bash
uv run python main.py                         # serve on configured host/port
uv run python main.py serve --reload          # DEVELOPMENT ONLY
uv run python main.py create-professor --username instructor
uv run python main.py cleanup-sessions
uv run python main.py backup --output /srv/pm-sim-backups
uv run python main.py serve --no-migrate      # DIAGNOSTICS ONLY
uv run python main.py batch scenario_examples/basic_project.json --repetitions 100
```

To migrate without starting or running a launcher command, use Alembic directly:

```bash
uv run alembic current
uv run alembic upgrade head
```

## Tests, fixtures, formatting, and linting

Tests live in `tests/test_<domain>.py`: engine unit tests cover pure rules, service tests cover
transactions/idempotency, API tests cover authentication/roles/status/error shapes, launcher
tests cover command dispatch, and database/backup tests cover infrastructure. Add a regression
test beside the closest domain rather than a miscellaneous test module.

Fixtures are intentionally local to the test module. Use pytest's `tmp_path` for each SQLite file,
create a fresh engine/session, create only the schema/data required by that test, and always close
the session and dispose the engine in fixture teardown. Prefer small named factory/helper functions
for simulation states over mutable global objects. Use fixed seeds and explicit timestamps; never
depend on execution order, a developer's `pm_sim.db`, wall-clock timing, or random output.

```bash
uv run ruff format .                          # write canonical formatting
uv run ruff format --check .                  # CI formatting check
uv run ruff check .                           # E/F/I/UP/B/SIM lint rules
uv run ruff check --fix .                     # review all automatic edits
uv run pytest                                 # complete suite
uv run pytest tests/test_api.py -q             # one module
uv run pytest tests/test_api.py::test_health -q # one node (use an existing node name)
uv run pytest -k 'replay or idempotency' -q     # expression across modules
uv run pytest tests/test_database.py -x -vv     # stop at first focused failure
```

## Alembic conventions and workflow

`alembic/env.py` replaces the INI URL with `DATABASE_URL`, imports `Base.metadata` for
autogeneration, uses `NullPool` online, and uses the application engine factory so SQLite foreign
keys, busy timeout, and WAL settings apply. Offline mode emits literal SQL, but generated SQL still
requires review for the target dialect. Version files form one chain via `revision` and
`down_revision`; use descriptive docstrings, typed identifiers, named indexes/constraints, and an
explicit `upgrade()`/`downgrade()`. Existing migrations are immutable once shared.

1. Change `app/db/models.py` and related service behavior.
2. Ensure the development database is at head, then generate a candidate:
   `uv run alembic revision --autogenerate -m 'describe change'`.
3. Review the whole file. Autogenerate cannot reliably infer renames, data backfills, constraint
   intent, server defaults, or safe ordering. Remove unrelated operations. Use portable SQLAlchemy
   types and named constraints. Use `op.batch_alter_table` where SQLite must rebuild a table.
4. Exercise a clean database and inspect the chain:

   ```bash
   DATABASE_URL=sqlite:////tmp/pm-sim-clean.db uv run alembic upgrade head
   DATABASE_URL=sqlite:////tmp/pm-sim-clean.db uv run alembic current
   uv run alembic history --verbose
   uv run alembic heads                         # must report one head
   ```

5. Create a database at the preceding revision, insert representative rows including null/edge
   JSON values, upgrade it, and assert the preserved/transformed data. Then test
   `uv run alembic downgrade -1` when reversal is truthful and safe, followed by re-upgrade.
   Destructive migrations may intentionally reject downgrade; document that in the revision and
   rely on the restore/rollback plan rather than pretending data can be recovered.
6. Run the complete checks. Before applying outside development: stop writers, make and verify a
   backup, upgrade once, validate readiness and application behavior, then reopen traffic.

Never use `app/db/create_schema.py` or `Base.metadata.create_all()` to repair a persistent database;
Alembic is the authoritative history. Never delete/stamp around a missing revision without first
identifying the database's provenance and restoring the matching code/history.

## PostgreSQL migration readiness

Changing `DATABASE_URL` alone is **not currently an approved PostgreSQL migration**. Before doing
so, all of the following must be completed and tested:

- Add and lock an appropriate SQLAlchemy PostgreSQL driver; none is currently declared.
- Run every migration, including downgrade paths, against a supported PostgreSQL version. Confirm
  batch alterations, constraint/index names, cascade behavior, transactionality, and one Alembic
  head. Continue using generic `String`, `Integer`, `DateTime(timezone=True)`, and `JSON`; avoid raw
  SQLite SQL, implicit row IDs, SQLite conflict syntax, and dialect-specific boolean/date behavior.
- Validate JSON round trips and comparisons, UTC aware timestamps, string UUID lengths, enum/string
  values, uniqueness/case sensitivity for usernames, foreign-key cascades, nullable backfills,
  integer ranges, and ordering assumptions on both databases.
- Test services for isolation and concurrency: optimistic run versions, idempotency uniqueness,
  atomic turn/audit transactions, lock/deadlock retry policy, connection pooling, timeouts, and
  multi-worker behavior. `SQLITE_*` settings will no longer provide concurrency controls.
- Rehearse data export/import with row counts, foreign keys, JSON/state digests, sequences (if
  introduced), and application-level replay checks. Freeze writes for the final cutover.
- Replace `main.py backup` with PostgreSQL-native, encrypted backups plus tested point-in-time or
  logical restore procedures. Define credentials, TLS, least privilege, rotation, monitoring, and
  rollback before production cutover.

## Troubleshooting

### Startup failure or invalid environment value

Read the first traceback before Uvicorn output. Validate settings with the one-line import above,
confirm Python 3.13 with `uv run python --version`, run `uv sync --frozen`, and verify the service's
working directory and environment. Port errors require freeing/changing `PORT`; database errors
require checking URL, parent directory, permissions, and connectivity. Do not add `--no-migrate`
merely to make a failing deployment appear healthy.

### Missing or inconsistent migrations

Run `uv run alembic current`, `uv run alembic heads`, and `uv run alembic history --verbose` using
the exact production environment. A missing table/column normally means `upgrade head` did not run.
If the recorded revision is absent from the checkout, deploy the matching code/migration history or
restore a compatible backup; do not use `create_all()`, edit `alembic_version`, or blindly `stamp`.

### Locked database

Stop duplicate application, Alembic, shell, and backup processes; inspect transactions and follow
the locking diagnostics in the SQLite guide. Keep WAL on a local filesystem and writes short. The
busy timeout absorbs brief contention only; repeated timeouts require finding the lock holder.

### Authentication cookie failure

Inspect the login response's `Set-Cookie` and the next request's `Cookie` in browser developer
tools. The frontend must send credentials and use the same origin. `COOKIE_SECURE=true` requires
browser-facing HTTPS; false is unsafe in production. Check host/path, `SameSite=Lax`, proxy scheme
and redirects, expiry/UTC clock, and whether cleanup removed an expired session. Password changes
and logout intentionally clear sessions.

### CORS failure

The application has no CORS middleware or allowlist setting. Serve frontend and `/api` from one
origin through the reverse proxy. If cross-origin architecture is required, implement an explicit
origin list and credentialed preflight tests; `*` is incompatible with safe cookie authentication.

### Stale simulation version (`409`)

Another request advanced the run. Fetch the run again, show the new state/version to the user, and
re-evaluate the decision. Do not blindly resubmit with a new idempotency key.

### Replay divergence

Preserve the database and logs. Compare engine version, scenario revision/snapshot and digest,
seed/turn seed, ordered decisions, authored-content checkpoints, request digest, idempotency key,
and resulting run version. Reproduce with the deployed code and a copy of the database. Never
rewrite published scenarios, historical turns, or snapshots to force equality; treat unexplained
divergence as data/engine compatibility work and block destructive migration.

### Corrupted or incompatible state

Stop writes and take a forensic copy. Run SQLite integrity/foreign-key checks on a copy, record the
Alembic revision and deployed commit, and validate stored JSON through the current state/scenario
models. Restore the newest verified compatible backup if checks fail. If integrity succeeds but
deserialization fails, deploy the code that understands that engine/schema version and perform a
reviewed migration—do not hand-edit JSON in place.

## Related documentation

- [Deployment](deployment.md)
- [SQLite classroom operations](sqlite-operations.md)
- [Backend testing](testing.md)
- [Architecture](architecture.md)
