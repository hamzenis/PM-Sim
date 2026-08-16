# SQLite classroom operations

SQLite is the initial classroom database. It is suitable for one application process and roughly
40–50 students when writes are short and transactional. It is not a shared-filesystem database and
does not support scaling PM-Sim across processes or hosts.

## Placement and filesystem permissions

Use an absolute URL such as `sqlite:////srv/pm-sim/data/pm_sim.db`. Keep the database on a reliable
local filesystem—not NFS, SMB, a synchronized folder, or an ephemeral release directory. The
service account needs traverse/write permission on the parent directory (SQLite creates journal,
WAL, SHM, and temporary files) and read/write permission on the database. No web server or unrelated
user should have access. As a starting point:

```bash
install -d -o pm-sim -g pm-sim -m 0750 /srv/pm-sim/data /srv/pm-sim-backups
chown pm-sim:pm-sim /srv/pm-sim/data/pm_sim.db
chmod 0640 /srv/pm-sim/data/pm_sim.db
```

Apply permissions through deployment tooling, not an interactive one-off, and ensure the backup
account can write its destination without making the live database broadly readable. Monitor free
space and inodes: WAL growth and backups need headroom.

## WAL, timeout, and concurrency

Every application and Alembic connection enables foreign keys and a configurable busy timeout.
File databases default to WAL plus `synchronous=NORMAL`:

```bash
DATABASE_URL=sqlite:////srv/pm-sim/data/pm_sim.db
SQLITE_BUSY_TIMEOUT_MS=5000
SQLITE_WAL=true
```

WAL lets readers coexist with a writer, but SQLite still permits only one writer. Committed pages
may remain in `pm_sim.db-wal` until checkpointed; `pm_sim.db-shm` coordinates connections. These are
live database components, not disposable files while the application runs. Long readers can prevent
checkpoint completion and grow the WAL. The busy timeout waits up to the configured milliseconds
for a transient lock; it neither breaks a lock nor makes long transactions safe.

Run exactly one Uvicorn worker and one host. Do not delete `-wal`/`-shm`, copy only `pm_sim.db`, or
toggle journal mode while connections are open. Move to PostgreSQL before multiple workers/hosts.

## Lock diagnostics

1. Record the error time and endpoint/job, then identify every process with the files open:
   `lsof /srv/pm-sim/data/pm_sim.db*` or `fuser -v /srv/pm-sim/data/pm_sim.db*`.
2. Check for duplicate backend instances, an interactive `sqlite3`, Alembic, restore/file-copy job,
   or transactions waiting on external work. Stop unauthorized writers gracefully.
3. Inspect without changing journal mode:

   ```bash
   sqlite3 /srv/pm-sim/data/pm_sim.db \
     'PRAGMA journal_mode; PRAGMA busy_timeout; PRAGMA wal_checkpoint(PASSIVE);'
   ```

   The checkpoint tuple reports busy/read/checkpointed frames; a persistent busy result or growing
   WAL points to a long-lived connection. `PASSIVE` does not force readers out.
4. Check disk space, filesystem/locality, ownership, and directory permissions. Review application
   logs for requests that opened a transaction and did not promptly commit/rollback.
5. After stopping all application processes, a normal connection may recover/checkpoint WAL. Never
   use `kill -9`, delete sidecars, or replace files as the first response. Increasing timeout is not
   a fix for repeat contention.

## Safe migration sequence

The launcher auto-migrates, but a controlled production migration should use a maintenance window:

1. Stop traffic and the application; confirm no process has the database open.
2. Create and verify an online backup with the currently deployed code.
3. Record `uv run alembic current` and the deployed commit; ensure the new checkout has one head.
4. Run `uv run alembic upgrade head` exactly once as the service account.
5. Run integrity/foreign-key checks, confirm `alembic current`, start one application process, and
   require `/health/ready` plus a representative authenticated read before reopening traffic.
6. Retain the pre-migration backup until the rollback window closes.

Do not let several replicas race startup migrations. Do not use schema `create_all()`. For a failed
destructive migration, stop and restore the pre-migration backup with the previous application;
only use Alembic downgrade when that revision's downgrade was explicitly tested with representative
data.

## Backup, verification, and retention

The launcher uses SQLite's backup API, which provides a consistent copy even with WAL activity:

```bash
uv run python main.py backup --output /srv/pm-sim-backups
```

Because the `backup` command migrates by default, production automation should normally run after a
successful deployment; if making a mandatory pre-migration backup, use the currently deployed code
and the command-specific `backup --no-migrate` controlled exception. Never substitute `cp pm_sim.db` while
the service is running.

Verify each generated file before declaring the job successful:

```bash
backup=/srv/pm-sim-backups/pm_sim-YYYYMMDD-HHMMSS-ffffff.db
test -s "$backup"
sqlite3 "$backup" 'PRAGMA integrity_check; PRAGMA foreign_key_check;'
sha256sum "$backup" > "$backup.sha256"
```

`integrity_check` must print `ok`; `foreign_key_check` must print no rows. Store the checksum and
metadata (UTC time, source host, app commit, Alembic revision) with the backup. Encrypt backups,
restrict access, and copy them to independent/off-host storage. Alert on missing, empty, or failed
verification jobs.

Adopt a documented retention policy aligned with institutional privacy and recovery objectives—for
example daily copies for 14 days, weekly for 8 weeks, and term-boundary copies through the required
grade-appeal period. This is an example, not a legal retention rule. Apply deletion to off-host
copies too, protect at least one generation from operator deletion, and perform scheduled restore
drills; retention without tested restoration is not recovery.

## Restore and validation

1. Stop the application and scheduled jobs; verify no open handles with `lsof`/`fuser.
2. Preserve the current database plus its `-wal`/`-shm` as a timestamped forensic set. Do not merge
   sidecars from different generations.
3. Verify the selected backup checksum, `integrity_check`, and `foreign_key_check` before copying.
4. Copy it to a new temporary path on the same filesystem, set service ownership/mode, then rename
   atomically to the configured database path. Ensure no stale destination sidecars remain.
5. With traffic still stopped, run `uv run alembic current`, deploy compatible code, and run
   `uv run alembic upgrade head` only if the restore plan calls for it.
6. Re-run integrity and foreign-key checks. Start one backend, require `/health/ready`, authenticate
   with a non-demo test/operator account, and sample counts plus a representative scenario/run.
   Where applicable, replay a known run and compare stored version/digests.
7. Reopen traffic only after validation. Retain both the forensic set and source backup until the
   incident is resolved.

Never overwrite a running SQLite database. A readiness response proves connectivity, not semantic
integrity or application/data-version compatibility.

## Related documentation

- [Deployment](deployment.md)
- [Development, migrations, and troubleshooting](development.md)
