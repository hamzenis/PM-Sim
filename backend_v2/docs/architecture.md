# Backend architecture

## Purpose and boundaries

`backend_v2` is the Python 3.13 rewrite of PM-Sim. It can run beside the legacy backend while
the existing frontend is migrated one feature at a time. The rewrite deliberately separates
the simulation rules from HTTP and persistence:

```text
browser
  -> FastAPI routes (app/api)
  -> application services (app/auth, app/classes, app/scenarios, app/simulations, app/results)
  -> SQLAlchemy models and sessions (app/db)

scenario definition
  -> scenario adapter (app/scenarios/to_simulation.py)
  -> pure simulation engine (app/simulation)
```

The modules in `app/simulation` must not import FastAPI, SQLAlchemy, or database models. This
keeps a simulation deterministic and makes the same engine usable by persisted HTTP runs and
the in-memory batch runner.

## Application layers

### HTTP API

`app/main.py` creates the FastAPI application and registers the route modules. Routes validate
input, resolve the current user, call an application service, and translate domain errors to
HTTP status codes. Business rules should not be duplicated in route functions.

The API groups are:

- `auth`: login, logout, current user, and password changes;
- `scenarios`: professor-owned scenario definitions and immutable revisions;
- `classes`: classes, students, and published scenario assignments;
- `simulations`: student runs, weekly decisions, turn history, and submission;
- `results`: professor views of class results and complete run audits;
- `audit`: professor-owned administrative activity history.

### Application services

Services enforce ownership, roles, lifecycle transitions, and transaction boundaries. A
mutating service commits the domain change and its audit record in the same transaction. Route
modules should not call `commit()` directly.

### Persistence

SQLAlchemy models live in `app/db/models.py`; schema changes are made through ordered Alembic
migrations in `alembic/versions`. SQLite is the default for a small classroom deployment.
Portable SQLAlchemy column types are used so PostgreSQL can be evaluated later without changing
the simulation layer.

Important persisted concepts are:

- **User**: professor or student credentials and role.
- **Auth session**: a hashed, expiring browser-session token.
- **Scenario**: professor-owned container that can be archived.
- **Scenario revision**: immutable numbered definition, initially `draft`, optionally
  `published`.
- **Class and membership**: professor-owned class and enrolled students.
- **Scenario availability**: assignment of a published revision to a class.
- **Simulation run**: a student's current state, version, seed, status, and final result.
- **Simulation turn**: append-only decision, deterministic turn seed, resulting state, events,
  and idempotency key.
- **Audit log**: append-only administrative action and non-secret metadata.

## Scenario lifecycle

1. A professor validates a scenario definition.
2. Uploading creates a scenario and draft revision 1.
3. Further edits create new draft revisions; published revisions are never edited in place.
4. The professor publishes a revision.
5. The published revision is assigned to one or more classes.
6. Enrolled students can discover that revision and start a run.
7. Archiving hides a scenario from normal professor lists but preserves revisions and historical
   runs.

## Simulation lifecycle

1. The student starts a run from an available published revision and supplies a seed.
2. The service converts the stored scenario definition into simulation inputs and creates the
   initial state.
3. Each weekly request contains a decision, the last observed run version, and an
   `Idempotency-Key` header.
4. The engine processes the decision from the stored state and a recorded turn seed.
5. The service atomically appends a turn and advances the run version.
6. A stale version returns `409 Conflict`; retrying the same idempotency key returns the already
   committed result rather than processing a second week.
7. The student submits the run. The final result and finish time are stored for professor
   reporting.

Student responses intentionally omit undiscovered bugs and incorrect specifications. Professor
run audits retain the complete persisted state and event history.

## Determinism and engine versions

A run stores its initial seed and engine version. Every turn stores its derived seed, submitted
decision, result, and events. Randomness enters the engine through an injected random source;
replaying the same versioned inputs therefore produces the same result.

Changing a formula or processing order must include tests and an engine-version decision.
Approved differences from the legacy implementation are recorded in
`docs/approved-redesigns.json`; deterministic golden fixtures protect the approved simplified
behavior.

## Operational model

`python main.py` applies migrations and starts one Uvicorn worker. A single process is the
supported SQLite mode. WAL, foreign keys, a busy timeout, and normal synchronization are enabled
by the database engine factory. The CLI also creates professor accounts, removes expired
sessions, and produces consistent SQLite backups.

No container runtime is required or assumed.
