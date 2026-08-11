# ADR 0001: Authored scenario content (Stages 1–3)

- **Status:** Approved
- **Scope:** Stages 1–3 authored narrative, questions, sequencing, and presentation effects

## Decision

Authored questions are answer-once. A required unanswered question blocks its checkpoint; an
optional item never does. Answers are recorded for presentation and teaching interaction only:
they are explicitly non-scoring, and `scoring` must be `null`.

The only approved effects are the schema's five presentation effects. Their bounded, explicit
payloads may display authored material or alter presentation flags/themes, but cannot mutate the
simulation. Unknown effects, simulation-state field names, and path, command, script, or
expression semantics are rejected at validation.

Authored content is completely separate from `SimulationState`, random sources, engine outcomes,
and `backend/app/simulation/results.py`. It must not affect simulation inputs, processing,
randomness, completion, scores, or results. The authored-content constants module therefore has
no import from `app.simulation`, and the scenario adapter ignores authored content.

Sequence checkpoints have a total order: `run_started`, then `before_week:N`, then
`after_week:N`, with week checkpoints interleaved in increasing `N`, and finally `run_finished`.
Dependencies cannot point forward in that order. Each object is presented at most once and each
entry is answerable/processed at most once.

## Approval boundary

Scored questions and any state-changing effect are outside Stages 1–3. Either requires separate
Product approval, Simulation Core approval, and its own ADR before schema or runtime work begins.

## Consequences

The backend validates the complete authored graph at import, revision creation, and again at
publication. Clients can safely render the content, but must not interpret payloads as executable
instructions or simulation changes.
