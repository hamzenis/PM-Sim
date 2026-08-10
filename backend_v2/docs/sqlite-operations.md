# SQLite classroom operations

SQLite is the initial classroom database. It is suitable for one application process and a
class of roughly 40–50 students, provided weekly writes remain short and transactional.

## Runtime defaults

Every application and Alembic connection enables foreign keys. File databases also default to
WAL journal mode, `synchronous=NORMAL`, and a 5000 ms busy timeout. Configure these with:

```bash
DATABASE_URL=sqlite:///./pm_sim.db
SQLITE_BUSY_TIMEOUT_MS=5000
SQLITE_WAL=true
```

Do not run multiple FastAPI worker processes with SQLite. Move to PostgreSQL before adding
multiple workers or deploying the application across multiple hosts.

## Deploying migrations

Stop the application, back up the database, and then run:

```bash
uv run alembic upgrade head
```

Migrations must finish successfully before restarting the application. Do not run automatic
schema creation in production.

## Backup

Create a consistent online backup using the Python launcher:

```bash
python main.py backup --output backups
```

Keep backups outside the deployment directory and periodically copy them to another machine.
Test restoration before the class begins.

## Restore

1. Stop the application.
2. Move the damaged database and any `-wal`/`-shm` files out of the deployment directory.
3. Copy the selected backup to `pm_sim.db`.
4. Run `uv run alembic upgrade head`.
5. Start the application and request `/health/ready`.

Never overwrite a running SQLite database with a file copy.
