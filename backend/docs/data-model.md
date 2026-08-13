# Data model

SQLAlchemy models in `app/db/models.py` persist users and sessions, professor-owned scenarios and
immutable revisions, classes and memberships, assignments, simulation runs and turn checkpoints,
authored-content responses, results, and audit records. Alembic revisions under `alembic/versions/`
are the authoritative schema history.

## Ownership and lifecycle

- A professor owns scenarios and classes.
- A published scenario revision is assigned to a class; existing assignments never follow later
  edits automatically.
- A student starts a simulation run from an assignment and advances it through weekly turns before
  submission.
- Audit records retain professor-visible administrative history.

API services define transaction boundaries. Keep engine state serialization behind the simulation
service and use portable SQLAlchemy types so PostgreSQL can replace SQLite later. Never edit a
deployed database schema directly; create and apply an Alembic migration.

## Related documentation

- [Backend architecture: persistence](architecture.md#persistence)
- [Development: migration workflow](development.md#alembic-conventions-and-workflow)
- [SQLite classroom operations](sqlite-operations.md)
- [HTTP API](api.md)
