# Simulation engine

The pure modules under `app/simulation/` calculate capacity, productivity, quality, staffing,
employee dynamics, task progress, and results for one weekly turn. They do not import FastAPI,
SQLAlchemy, or database code. `app/simulations/service.py` owns persistence and invokes the engine;
`app/batch/` invokes the same engine over deterministic seeds for scenario balancing.

## Lifecycle and determinism

The application maps a published scenario revision into engine input, restores the persisted state,
validates the weekly decision, advances exactly one turn, and stores a checkpoint. Random choices are
derived from the run seed. Given the same engine version, scenario revision, seed, state, and decision,
the result must be reproducible.

The built-in `development-first`, `balanced`, `quality-first`, and `overtime-heavy` batch strategies
are balancing baselines, not models of student behaviour.

## Change checklist

1. Keep calculation code independent of HTTP and persistence concerns.
2. Add focused unit tests and deterministic replay coverage.
3. Decide whether serialized state or the engine version must change.
4. Check authored-content triggers and effects against the new turn behaviour.
5. Update the API documentation if input or result projections change.

## Related documentation

- [Backend architecture](architecture.md#simulation-lifecycle)
- [Authored scenario content](authored-content.md)
- [Data model](data-model.md)
- [Backend testing](testing.md)
