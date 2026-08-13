# Frontend UX sign-off — 2026-08-13

## Scope and outcome

All routes in `src/Routing.jsx` were reviewed in their applicable unauthenticated, student, and
professor contexts. Critical login, student scenario/start/weekly-decision, professor class
management, and professor result-review flows were exercised at desktop and Pixel 7 widths.

**Sign-off:** both the professor and student interfaces are ready for ordinary classroom use.

## Before / after

Before the redesign, workflows exposed implementation-oriented data and used uneven feedback,
spacing, and responsive behaviour. After the redesign, the scenario and simulation paths lead with
teaching labels and progress; professor class/results workflows use task-oriented panels; shared
loading, empty, error, status, formatting, confirmation, focus, and mobile patterns are in place.

Representative after screenshots are the desktop and mobile baselines in
`tests/visual/__screenshots__` for login, student scenarios, the weekly decision, professor class
management, and professor result summary. These are the maintained comparison evidence for future
before/after reviews.

## Route review

| Audience | Routes reviewed | Result |
| --- | --- | --- |
| Public | `/`, `/login`, unknown route | Correct landing/login content and redirects. |
| Student | `/scenarios`, `/simulations/:run_id`, `/help`, `/change-password`, unknown route | Assignment, resume/start, briefing, weekly decision, submission confirmation, and support paths are classroom-ready. |
| Professor | `/scenarios`, `/classes`, `/classes/:class_id/results/:run_id`, `/audit`, `/help`, `/change-password` | Scenario, roster, assignment, result, technical audit, and account paths are classroom-ready. |

## Identity exposure audit

Rendered source was searched for UUIDs; raw run, class, scenario-revision, and employee IDs; and
digests/hashes.

- **Correctly hidden internal identities:** API modules, route parameters, React keys, selection
  values, assignment matching, idempotency UUIDs, and DOM targeting use IDs without rendering them.
  Employee dismissal controls show the employee-type display label, not the employee ID.
- **Intentionally available:** professor result audit identifiers, engine/seed metadata, definition
  and projection digests, and raw audit JSON are inside the closed `Technical details` disclosure.
- **Accidental exposure:** none found in ordinary student or professor workflow copy. Automated
  tests assert that representative UUIDs stay hidden until professor technical details are opened.

## Compatibility / backend boundary

The redesign commits were inspected for backend impact. Backend work is additive API, auth, class,
scenario, audit, and authored-content support; it does not replace the simulation calculations,
scoring equations, random-seed behaviour, staffing rules, productivity rules, or persistence
identity. The backend engine, randomness, staffing, productivity, state-codec, persistence, API, and
integration suites all pass, providing regression coverage for that boundary.

## Follow-up notes

- `npm ci` reports dependency audit findings (two moderate and two high); remediation should be a
  separately reviewed dependency change rather than part of UX sign-off.
- Vite reports a production chunk above 500 kB. This does not block classroom use, but route-level
  code splitting is a reasonable future performance task.
