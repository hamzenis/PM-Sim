# Scenario authoring

This guide is the user manual for schema version `1`. The executable authority is
`app/scenarios/models.py`; validate a file with `ScenarioDefinition.model_validate_json(...)`
before upload. Unknown keys are errors at every level. The architecture decisions behind the
content boundary and persistence are recorded in [ADR 0001](adr/0001-authored-scenario-content.md)
and [ADR 0002](adr/0002-content-persistence-idempotency.md); use this guide, rather than the ADRs,
for authoring instructions.

## Complete top-level schema

| Field | Required | Type, range, and default |
| --- | --- | --- |
| `schema_version` | yes | Integer literal `1`. |
| `name` | yes | Non-empty string. |
| `description` | no | String, default `""`; presentation only. |
| `project` | yes | Project object below. |
| `tasks` | yes | Task object below. |
| `employee_types` | yes | Non-empty array; `code` values must be unique. |
| `rules` | no | Rule object; all members have defaults. |
| `scoring` | no | Scoring object; all members have defaults. |
| `authored_content` | yes | Authored-content object; use four empty arrays when no content is needed. |

### Project, tasks, employees, rules, and scoring

| Path | Required | Valid values and default |
| --- | --- | --- |
| `project.budget` | yes | Number `>= 0`; currency units. |
| `project.working_days` | yes | Integer `> 0`. |
| `project.hours_per_day` | no | Integer `1..24`, default `8`. |
| `project.working_days_per_week` | no | Integer `1..7`, default `5`. |
| `tasks.total` | yes | Integer `> 0`. |
| `tasks.difficulty_distribution` | no | Object, default `{easy: .25, medium: .50, hard: .25}`. Each member is `0..1`, and the three must total `1.0` within `1e-9`. Omitted members take their individual defaults. |
| `employee_types[].code` | yes | Stable machine key matching `^[a-z][a-z0-9_]*$`; unique within the scenario. |
| `employee_types[].name` | yes | Non-empty display string. |
| `employee_types[].cost_per_day` | yes | Number `>= 0`, in the same currency units as budget. |
| `employee_types[].throughput.{easy,medium,hard}` | yes | Number `>= 0`; tasks per eight productive hours. |
| `employee_types[].error_rate` | yes | Probability `0..1`. |
| `employee_types[].management_skill` | no | Probability `0..1`, default `0`. |
| `rules.randomness` | no | `"full"`, `"semi"`, or `"none"`; default `"full"`. |
| `rules.stress_overtime_increase` | no | Probability `0..1`, default `.05`, applied per overtime hour. |
| `rules.stress_weekend_reduction` | no | Probability `0..1`, default `.20`, applied once per turn. |
| `rules.overtime_motivation_decrease` | no | Probability `0..1`, default `.02`, per overtime hour. |
| `rules.solo_stress_increase` | no | Probability `0..1`, default `.05`, once per turn for a one-person team. |
| `rules.meeting_familiarity_increase` | no | Probability `0..1`, default `.05`, per meeting hour per employee. |
| `rules.training_skill_increase_rate` | no | Number `>= 0`, default `.10`. |
| `rules.training_motivation_boost` | no | Probability `0..1`, default `.10`, per training hour. |
| `rules.integration_test_days` | no | Integer `>= 0`, default `1`. Reserved schema value; the current weekly engine does not consume it. |
| `scoring.{quality,time,budget}_limit` | no | Integer `>= 0`, each default `100`; component point weights. |
| `scoring.{quality,time,budget}_exponent` | no | Number `>= 0`, each default `1`; curve shapes. |

JSON numbers must not rely on `NaN` or infinity. The schema deliberately has no initial team:
students hire employees through weekly decisions. See [Simulation engine](simulation-engine.md) for
how these values behave.

## Authored content

`authored_content` requires `fragments`, `questions`, `events`, and `sequence`, each an array (empty
is valid). Authored content is presentation and teaching interaction only: answers are not scored
and effects cannot change simulation state, randomness, outcomes, or scores.

### Stable identifiers and definitions

Every fragment, question, event, sequence entry, question option, flag, theme, and referenced
presentation ID uses a lowercase authored ID matching `^[a-z][a-z0-9_-]{0,63}$`. Treat IDs as
durable API keys: do not derive them from editable display text or reuse an old ID for a different
meaning. Fragment, question, event, and sequence-entry IDs share one global namespace and must be
unique. Option IDs need only be unique within their question.

| Definition | Fields |
| --- | --- |
| Fragment | Required `id`, `body` (1–500 characters); optional `title` (1–500 when present) and `required` (default `false`). A required fragment must be acknowledged; an optional one completes on delivery. |
| Question | Required `id`, `prompt` (1–500), `answer_schema`; `options` defaults `[]`; `feedback_by_option` defaults `{}`; `scoring` may only be `null` and defaults to `null`; `required` defaults `true`; `answer_once` may only be `true` and defaults `true`; `short_text_max_length` is optional integer `1..500`. |
| Event | Required `id` and non-empty `effects`; `professor_only` defaults `false`. Professor-only events are omitted from student serialization. |

Choice questions (`single_choice` or `multiple_choice`) require at least two options, each with
`id` and a 1–500 character `label`. Boolean and short-text questions must have no options.
`feedback_by_option` maps option IDs to 1–500 character feedback and cannot mention an unknown
option. `short_text_max_length` is legal only for `short_text`; absent means the runtime maximum is
500. Runtime answers are respectively an option-ID string, an array of unique option IDs (stored in
definition order), a JSON boolean, or a string. Empty arrays/strings are rejected only for required
questions. Questions cannot be answered twice; there is no skip-as-answer command.

### Sequence, checkpoints, ordering, and visibility

Each sequence entry requires `id`, `trigger`, and **exactly one** of `fragment_id`, `question_id`, or
`event_id`. Optional fields are `depends_on: []`, `priority: 0`, `visibility: "default"`, and
`visibility_associated_entry_id: null`. Every reference must resolve, and each authored object may
appear in the sequence only once. Dependencies must exist, be unique, exclude the entry itself,
form an acyclic graph, and never point from an earlier checkpoint to a later one.

Triggers are `{ "type": "run_started" }`, `{ "type": "before_week", "week": N }`,
`{ "type": "after_week", "week": N }`, and `{ "type": "run_finished" }`, where `N >= 1`.
Their order is run start, each week's before/after checkpoints, then run finish. Once a checkpoint
has been reached, eligible entries whose dependencies are complete are sorted by ascending
`priority`, then original sequence-array position. Optional entries are actionable together, but
only the earliest required entry is actionable, creating a required-content gate. Required
questions wait for an answer; required fragments wait for acknowledgement. Events and optional
fragments complete on delivery. Optional questions remain actionable until answered but do not
block later required work.

Visibility controls serialization, not trigger eligibility:

* `default` exposes otherwise eligible content normally.
* `run_finished` exposes it only at terminal projection.
* `after_acknowledgement` requires `visibility_associated_entry_id`. That association must name a
  sequence entry referencing a **required fragment**. Before it completes, only the dependent
  item's ID/title are exposed; afterward its body/prompt may be exposed.

### Presentation effects

Every effect has `type` and `payload`; its compact JSON payload is limited to 4,096 bytes.

| Type | Exact payload | Result |
| --- | --- | --- |
| `show_message` | `{ "text": <1–500 chars> }` | Append a message. |
| `show_fragment` | `{ "fragment_id": <authored ID> }` | Reveal that fragment ID. |
| `show_question` | `{ "question_id": <authored ID> }` | Reveal that question ID. |
| `set_presentation_flag` | `{ "flag": <authored ID>, "value": <boolean> }` | Set a UI flag. |
| `set_presentation_theme` | `{ "theme": <authored ID> }` | Set the UI theme. |

Effects run in listed order. Payloads are strict data, never executable code; state-like and
command/path/script semantics are rejected. A shown ID is a presentation reference and is not an
extra sequence use. Feedback and effects are teaching/UI output only.

## Annotated examples

The comments below make the examples JSONC for explanation; remove comments before validation.

### Minimal

```jsonc
{
  "schema_version": 1,
  "name": "Minimum valid scenario",
  "project": { "budget": 10000, "working_days": 10 }, // hour/week defaults apply
  "tasks": { "total": 20 },                           // 25/50/25 distribution
  "employee_types": [{
    "code": "developer", "name": "Developer", "cost_per_day": 200,
    "throughput": { "easy": 4, "medium": 2, "hard": 1 },
    "error_rate": 0.04
  }],
  "authored_content": { "fragments": [], "questions": [], "events": [], "sequence": [] }
}
```

### Intermediate

```jsonc
{
  "schema_version": 1, "name": "Briefed project",
  "description": "Read the brief and choose a priority.",
  "project": { "budget": 30000, "working_days": 20, "working_days_per_week": 5 },
  "tasks": { "total": 60, "difficulty_distribution": { "easy": 0.3, "medium": 0.5, "hard": 0.2 } },
  "employee_types": [{ "code": "developer", "name": "Developer", "cost_per_day": 240,
    "throughput": { "easy": 5, "medium": 2.5, "hard": 1 }, "error_rate": 0.05,
    "management_skill": 0.4 }],
  "rules": { "randomness": "semi" },
  "authored_content": {
    "fragments": [{ "id": "brief", "body": "Review scope.", "required": true }],
    "questions": [{ "id": "priority", "prompt": "Primary goal?", "answer_schema": "single_choice",
      "options": [{ "id": "quality", "label": "Quality" }, { "id": "speed", "label": "Speed" }],
      "feedback_by_option": { "quality": "Plan testing capacity." } }],
    "events": [],
    "sequence": [
      { "id": "seq_brief", "trigger": { "type": "run_started" }, "fragment_id": "brief" },
      { "id": "seq_priority", "trigger": { "type": "run_started" }, "question_id": "priority",
        "depends_on": ["seq_brief"] } // acknowledgement unlocks the question
    ]
  }
}
```

### Comprehensive

This shortened comprehensive example combines visibility, every definition kind, an effect, and
terminal content. Comments identify constraints; remove them before validation.

```jsonc
{
  "schema_version": 1, "name": "Content lifecycle",
  "project": { "budget": 50000, "working_days": 25, "hours_per_day": 8 },
  "tasks": { "total": 100 },
  "employee_types": [{ "code": "lead", "name": "Technical lead", "cost_per_day": 300,
    "throughput": { "easy": 6, "medium": 3, "hard": 1 }, "error_rate": 0.03,
    "management_skill": 0.7 }],
  "rules": { "randomness": "full", "training_skill_increase_rate": 0.12 },
  "scoring": { "quality_limit": 150, "time_limit": 100, "budget_limit": 50 },
  "authored_content": {
    "fragments": [
      { "id": "brief", "title": "Brief", "body": "Acknowledge the brief.", "required": true },
      { "id": "week_hint", "body": "Inspect quality before adding scope." }
    ],
    "questions": [
      { "id": "tradeoff", "prompt": "Select trade-offs.", "answer_schema": "multiple_choice",
        "options": [{ "id": "scope", "label": "Scope" }, { "id": "quality", "label": "Quality" }],
        "feedback_by_option": { "quality": "Explain the testing allocation." }, "required": false },
      { "id": "reflection", "prompt": "Summarize the result.", "answer_schema": "short_text",
        "short_text_max_length": 250 }
    ],
    "events": [{ "id": "notice", "effects": [
      { "type": "show_message", "payload": { "text": "The first week is complete." } },
      { "type": "set_presentation_flag", "payload": { "flag": "review_ready", "value": true } }
    ] }],
    "sequence": [
      { "id": "seq_brief", "trigger": { "type": "run_started" }, "fragment_id": "brief",
        "priority": -10 }, // lower priority numbers resolve first
      { "id": "seq_tradeoff", "trigger": { "type": "before_week", "week": 1 },
        "question_id": "tradeoff", "depends_on": ["seq_brief"] },
      { "id": "seq_hint", "trigger": { "type": "before_week", "week": 1 },
        "fragment_id": "week_hint", "visibility": "after_acknowledgement",
        "visibility_associated_entry_id": "seq_brief" },
      { "id": "seq_notice", "trigger": { "type": "after_week", "week": 1 },
        "event_id": "notice", "depends_on": ["seq_tradeoff"] },
      { "id": "seq_reflection", "trigger": { "type": "run_finished" },
        "question_id": "reflection", "depends_on": ["seq_notice"], "visibility": "run_finished" }
    ]
  }
}
```

The repository showcase additionally exercises all four answer formats, optional/required content,
professor-only events, and every checkpoint. Read
[`scenario_examples/authored_content_comprehensive.json`](../scenario_examples/authored_content_comprehensive.json)
as the canonical comprehensive valid JSON, and follow its sequence from `s_briefing` through
`s_professor`. For a compact simulation-focused starting point, copy
[`scenario_examples/basic_project.json`](../scenario_examples/basic_project.json).

## Revisions, publication, and immutability

Creating a scenario creates draft revision 1; later edits should append revision 2, 3, and so on.
The scenario ID is the long-lived container, while the revision ID/number identifies an exact
definition. Publication revalidates the complete stored JSON, changes `draft` to `published`, and
pins new runs to that revision. A published definition is an immutable historical input: never
edit its JSON or reinterpret its stable IDs. Create and publish a new revision instead; existing
runs continue reading detached definitions from their pinned revision. Delivery/response records
and canonical request digests preserve retries and audit history as described by
[ADR 0002](adr/0002-content-persistence-idempotency.md).

## Scenario-validation checklist

- [ ] Parse as strict JSON (no comments), then validate with `ScenarioDefinition`.
- [ ] Confirm units, ranges, defaults, unique employee codes, and a distribution totaling `1.0`.
- [ ] Check every authored ID for stability, pattern, uniqueness, and resolved single use.
- [ ] Check choice shapes, feedback keys, text limits, effect allowlist, and payload size.
- [ ] Walk checkpoints and dependencies; check acyclicity, required gates, and terminal content.
- [ ] Test student and professor views, acknowledgement/answer flows, and all visibility modes.
- [ ] Review simulation balance with the workflow below and the engine guide.
- [ ] Perform a final publication review; after publishing, make corrections in a new revision.

## Balancing workflow

1. Validate the draft and start with `randomness: "none"` to expose capacity and task-flow errors.
2. Exercise boundary cases: zero budget, one employee, short final weeks, zero throughput for a
   difficulty, maximum/minimum distributions, overtime, and allocations concentrated in one stage.
3. Switch to the intended randomness mode. Run every candidate with the same consecutive seed
   range and repetitions; save both JSON and CSV reports.
4. Compare `development-first`, `balanced`, `quality-first`, and `overtime-heavy` as coarse
   baselines—not predicted student play. Add scenario-specific strategies for realistic choices.
5. Inspect individual outlier seeds as well as completion/exhaustion rates and averages. Replay a
   seed after each adjustment; change one parameter group at a time.
6. Repeat against the previous revision with identical seeds, then review briefing/content timing,
   identifiers, defaults, and batch evidence before publication.

## Related documentation

- [Simulation engine and batch analysis](simulation-engine.md)
- [Authored-content architecture overview](authored-content.md)
- [ADR 0001: authored scenario content](adr/0001-authored-scenario-content.md)
- [ADR 0002: content persistence and idempotency](adr/0002-content-persistence-idempotency.md)
