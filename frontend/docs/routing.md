# Routing and role gates

Routes are declared in `src/Routing.jsx` inside public, authenticated, or professor-only gates.
Register new pages there and ensure loading and authorization checks do not briefly expose protected
content.

## Professor workflows

- `/scenarios`: create, revise, publish, and archive scenarios.
- `/classes`: manage classes, students, assignments, and results.
- `/classes/:class_id/results/:run_id`: audit a submitted simulation run.
- `/audit`: review administrative history.

## Student workflows

- `/scenarios`: review assignments and start or resume simulation runs.
- `/simulations/:run_id`: make weekly decisions, review history, and submit a final result.

## Shared workflows

- `/login`: authenticate.
- `/change-password`: change the current user's password.

Use API identifiers in route parameters and request keys, but show names and human-readable labels in
ordinary page copy.

## Related documentation

- [Authentication](authentication.md)
- [UI guidelines](ui-guidelines.md)
