# HTTP API contract and workflows

## Authority, base URL, and conventions

The local default is `http://127.0.0.1:8000`. API routers are mounted below `/api`;
the two health routes are not. The running FastAPI document at `/openapi.json` (and its
interactive rendering at `/docs`) is **authoritative for generated request and response
schemas**. This guide complements it with workflows, invariants, visibility rules, retry
semantics, and lifecycle behavior. If a generated schema and this document differ, fix this
document and treat the running schema as correct.

Unless stated otherwise, requests and responses are JSON. Request models use Pydantic and
reject unknown properties where their model declares `extra="forbid"`. Path identifiers are
case-sensitive opaque strings. Successful `204` responses have no body.

### Roles

* **Public** needs no cookie.
* **Authenticated** accepts either a student or professor session and restricts user-owned
  resources to that user.
* **Professor** additionally requires `role == "professor"`. Ownership checks deliberately
  make another professor's class, scenario, or result appear missing.

Every protected endpoint can return `401`; every professor endpoint can additionally return
`403`. Every request can return `422` when a path, query, header, or body fails FastAPI/Pydantic
validation.

## Errors

The common FastAPI/application error envelope is:

```json
{"detail":"human-readable explanation"}
```

Pydantic/FastAPI `422` responses use the same top-level `detail`, but its value is an array of
structured validation entries (`loc`, `msg`, `type`, and sometimes `ctx`/`input`). The one
domain-specific structured error is a blocked weekly turn:

```json
{
  "detail": {
    "code": "content_blocked",
    "message": "required content must be completed",
    "blocking_entry": {"id":"delivery_opaque","sequence_entry_id":"entry_opaque","kind":"question","status":"actionable","checkpoint":"before_week:2","required":true,"visible":true}
  }
}
```

Error categories are intentionally distinguished by HTTP status, not by stable message text:

| Category | Status | Meaning and client action |
| --- | --- | --- |
| Authentication | `401` | Cookie absent, unknown, or expired; return to login. Login also uses this for bad credentials. |
| Authorization | `403` | Valid user lacks professor role; do not retry with the same principal. |
| Validation | `422` | Transport/schema constraint failed (including a missing idempotency header); correct the request. Domain-invalid input may instead be `400`. |
| Missing/hidden resource | `404` | Resource does not exist, is not owned/visible, or membership/assignment is missing where the decorator maps it to 404. |
| Lifecycle conflict | `400` or `409` | Operation is invalid in the current state. Scenario archive conflicts are `409`; most run decisions/start errors are `400`; a content gate is structured `409`. |
| Idempotency conflict | `409` | A key already names a different canonical command; never retry that changed command under the key. |
| Concurrent version | `409` | `expected_version` is stale; refetch, review, and make a new command. |

`detail` strings are display/debug text, not stable machine codes. Network/proxy errors and
`500` remain possible and are not endpoint business outcomes.

## Authentication, cookies, and CORS

### Cookie lifecycle

`POST /api/auth/login` normalizes the username by trimming and lowercasing it, verifies the
scrypt password hash, creates a random server-side session, and returns the user. It sets
`pm_sim_session` with `HttpOnly`, `SameSite=Lax`, an absolute expiry, and `Secure` controlled by
`COOKIE_SECURE` (false locally; enable it under HTTPS). The default lifetime is eight hours and
is configurable through `SESSION_LIFETIME_HOURS`. Tokens are stored server-side only as SHA-256
digests. An expired cookie is rejected, and its server record is deleted when used.

Browser clients must use credentialed requests (for example `fetch(..., {credentials:
"include"})`) whenever frontend and API origins differ. The application currently installs no
`CORSMiddleware`, so it works as same-origin by default; a cross-origin deployment must install
or supply CORS at the edge with the **exact allowed frontend origin**, credentials enabled, and
the needed methods/headers (including `Content-Type` and `Idempotency-Key`). A wildcard
`Access-Control-Allow-Origin: *` cannot be used with credentialed cookies.

Logout is safe without a valid cookie: `POST /api/auth/logout` deletes the matching server
session when present and always expires the browser cookie. Password changes require the
current password; a successful change replaces the scrypt hash, revokes **all** sessions for
the user (including the current one), clears this response's cookie, and therefore requires a
fresh login. Professor password resets for students likewise replace the password and revoke
that student's sessions.

New and reset passwords are 10–200 characters at the HTTP boundary. The auth service itself
enforces the minimum of 10. There are no composition requirements. Usernames created/imported
by services are trimmed and lowercased; they must be non-empty and unique. Professors are made
with the local CLI, not public registration.

```http
POST /api/auth/login
Content-Type: application/json

{"username":"student.demo","password":"sanitized-password"}
```

```http
HTTP/1.1 200 OK
Set-Cookie: pm_sim_session=<redacted>; HttpOnly; SameSite=lax; Expires=...

{"id":"usr_opaque","username":"student.demo","role":"student"}
```

### Authentication endpoints

| Method/path | Role | Input | Success | Response | Meaningful errors |
| --- | --- | --- | --- | --- | --- |
| `POST /api/auth/login` | Public | `LoginRequest {username:string, password:string}` | `200` | `UserResponse {id, username, role}` plus cookie | `401` invalid username/password; `422` malformed body. |
| `POST /api/auth/logout` | Public (cookie optional) | No body; optional session cookie | `204` | None; cookie cleared | No domain errors. |
| `GET /api/auth/me` | Authenticated | None | `200` | `UserResponse` | `401`. |
| `PUT /api/auth/password` | Authenticated | `{current_password:string, new_password:string(10..200)}` | `204` | None; all sessions revoked and cookie cleared | `400` current password wrong/service password rule; `401`; `422`. |

## System endpoints

| Method/path | Role | Input | Success/response | Meaningful errors |
| --- | --- | --- | --- | --- |
| `GET /health` | Public | None | `200 {"status":"ok"}` | No domain errors. |
| `GET /health/ready` | Public | None | `200 {"status":"ready"}` | `503 {"detail":"database unavailable"}`. |

## Scenario authoring

All routes below require a professor. `ScenarioDefinition` is the generated OpenAPI schema for
the complete authored scenario; it includes scenario metadata, initial state, employee types,
rules/scoring, and authored-content sequence. Validation normalizes through Pydantic but does
not persist anything. State-changing effects and scored authored questions are rejected:
authored interactions are presentation/learning content only.

| Method/path | Input | Success | Response schema | Meaningful endpoint errors |
| --- | --- | --- | --- | --- |
| `POST /api/scenarios/validate` | Body `ScenarioDefinition` | `200` | normalized `ScenarioDefinition` | `401`, `403`, `422` including cross-field scenario/content validation. |
| `POST /api/scenarios` | Body `ScenarioDefinition` | `201` | `RevisionResponse` | `401`, `403`, `422`; persistence failures may be `500`. |
| `GET /api/scenarios` | None | `200` | `ScenarioSummary[]` | `401`, `403`. |
| `GET /api/scenarios/{scenario_id}` | Opaque path ID | `200` | owned `RevisionResponse[]` | `404` missing/not owned; auth errors. |
| `POST /api/scenarios/{scenario_id}/revisions` | Body `ScenarioDefinition` | `201` | `RevisionResponse` | `404` missing/not owned; `409` archived; `422`; auth errors. |
| `POST /api/scenarios/{scenario_id}/revisions/{revision_number}/publish` | Integer revision path parameter; no body | `200` | `RevisionResponse` | `404` scenario/revision missing or hidden; `409` archived; `422`; auth errors. |
| `POST /api/scenarios/{scenario_id}/archive` | Opaque path ID; no body | `204` | None | `404` missing/not owned; auth errors. |

Schemas used above:

* `RevisionResponse`: `{id, scenario_id, revision_number:int, schema_version:int,
  status:string, definition:object, created_at:datetime, published_at:datetime|null}`.
* `ScenarioSummary`: `{id, name, latest_revision:int, latest_status:string}`.

Sanitized validation/import and publication flow:

```http
POST /api/scenarios/validate
Content-Type: application/json

{
  "schema_version": 1,
  "name": "Sanitized onboarding scenario",
  "description": "Practice schedule and quality trade-offs.",
  "project": {"budget":100000,"working_days":20,"hours_per_day":8,"working_days_per_week":5},
  "tasks": {"total":120,"difficulty_distribution":{"easy":0.25,"medium":0.5,"hard":0.25}},
  "employee_types": [{"code":"developer","name":"Developer","cost_per_day":400,"throughput":{"easy":4,"medium":2,"hard":1},"error_rate":0.03,"management_skill":0.2}],
  "rules": {"randomness":"semi","integration_test_days":1},
  "scoring": {"quality_limit":100,"time_limit":100,"budget_limit":100,"quality_exponent":1,"time_exponent":1,"budget_exponent":1},
  "authored_content": {"fragments":[],"questions":[],"events":[],"sequence":[]}
}
```

The exact required definition properties evolve; copy a valid shape from `/openapi.json` and
use the normalized `200` body as the body for `POST /api/scenarios`. Creation returns revision
1 in `draft` state. Publish it with:

```http
POST /api/scenarios/scn_opaque/revisions/1/publish

HTTP/1.1 200 OK
{"id":"rev_opaque","scenario_id":"scn_opaque","revision_number":1,"schema_version":1,"status":"published","definition":{"...":"sanitized"},"created_at":"2026-08-13T10:00:00Z","published_at":"2026-08-13T10:05:00Z"}
```

## Classes, students, and assignments

All routes are professor-only except `available-scenarios`, which is authenticated. Professor
routes enforce ownership; archived classes are excluded from listing and reject operations
that require an active class.

| Method/path | Input | Success | Response schema | Meaningful endpoint errors |
| --- | --- | --- | --- | --- |
| `POST /api/classes` | `{name:string}` | `201` | `ClassResponse` | `400` blank name/professor missing; auth/`422`. |
| `GET /api/classes` | None | `200` | `ClassResponse[]` | Auth errors. |
| `PATCH /api/classes/{class_id}` | `{name:string}` | `200` | `ClassResponse` | `400` missing/hidden/archived or blank name; auth/`422`. |
| `POST /api/classes/{class_id}/archive` | No body | `204` | None | `404` missing/hidden/archived; auth. |
| `GET /api/classes/{class_id}/students` | None | `200` | `StudentResponse[]` | `404` missing/hidden/archived; auth. |
| `POST /api/classes/{class_id}/students/import` | `{students:[{username:string(1..100), password:string(10..200)}]}`; 1–100 items | `201` | created `StudentResponse[]` | `409` duplicate input/existing username, missing/archived class, or transaction conflict; auth/`422`. |
| `POST /api/classes/{class_id}/students` | `{username:string}` | `201` | `{membership_id:string}` | `404` class/student missing, hidden, archived, or membership service error; auth/`422`. |
| `DELETE /api/classes/{class_id}/students/{student_id}` | Path IDs; no body | `204` | None | `404` class/membership missing or hidden; auth. |
| `PUT /api/classes/{class_id}/students/{student_id}/password` | `{new_password:string(10..200)}` | `204` | None | `404` class/membership missing or hidden (and mapped password service errors); auth/`422`. |
| `GET /api/classes/{class_id}/scenarios` | None | `200` | `AssignedScenarioResponse[]` | `404` class missing/hidden/archived; auth. |
| `POST /api/classes/{class_id}/scenarios` | `{scenario_revision_id:string}` | `201` | `AvailabilityResponse` | `404` class/revision missing, hidden, archived, or revision not published; auth/`422`. |
| `DELETE /api/classes/{class_id}/scenarios/{scenario_revision_id}` | Path IDs; no body | `204` | None | `404` class/assignment missing or hidden; auth. |
| `GET /api/classes/available-scenarios` | Authenticated; no input | `200` | `AvailableScenarioResponse[]` | `401`. |

Response shapes: `ClassResponse {id,name,professor_id}`; `StudentResponse {id,username}`;
`AvailabilityResponse {id,scenario_revision_id,created_at}`; `AssignedScenarioResponse
{id,scenario_id,scenario_name,revision_number,status}`; `AvailableScenarioResponse
{id,class_id,class_name,revision_number,definition}`. Here the available item's `id` is the
scenario **revision ID**. The same revision can occur once per assigned class.

```http
POST /api/classes
Content-Type: application/json

{"name":"Section A (sanitized)"}
```

```http
POST /api/classes/cls_opaque/students/import
Content-Type: application/json

{"students":[{"username":"student.one","password":"temporary-pass-01"},{"username":"student.two","password":"temporary-pass-02"}]}
```

```http
POST /api/classes/cls_opaque/students
Content-Type: application/json

{"username":"existing.student"}
```

```http
PUT /api/classes/cls_opaque/students/usr_opaque/password
Content-Type: application/json

{"new_password":"replacement-pass-01"}
```

```http
POST /api/classes/cls_opaque/scenarios
Content-Type: application/json

{"scenario_revision_id":"rev_opaque"}

HTTP/1.1 201 Created
{"id":"assignment_opaque","scenario_revision_id":"rev_opaque","created_at":"2026-08-13T11:00:00Z"}
```

## Simulation runs and authored content

All routes are authenticated and expose only runs owned by the current user. A professor does
not gain access to a student's player routes; professor inspection uses result routes.

### Endpoint inventory

| Method/path | Input | Success | Response schema | Meaningful endpoint errors |
| --- | --- | --- | --- | --- |
| `POST /api/simulations` | `StartSimulationRequest {scenario_revision_id, class_id:string  null = null, seed:int}` | `201` | `RunResponse` | `400` user/revision/scenario unavailable, unpublished, inaccessible, or invalid class association; `401`; `422`. |
| `GET /api/simulations` | None | `200` | `RunSummaryResponse[]` | `401`. |
| `GET /api/simulations/{run_id}` | Path ID | `200` | `RunResponse` | `404` missing/not owned; `401`. |
| `GET /api/simulations/{run_id}/turns` | Path ID | `200` | `TurnHistoryResponse[]` | `404` missing/not owned; `401`. |
| `POST /api/simulations/{run_id}/turns` | Required `Idempotency-Key` header (1..100 chars); `CompleteTurnRequest` | `200` | `TurnResponse` | `400` missing/not-owned/inactive run or invalid domain decision; `409` stale version, conflicting key, or structured content gate; `401`; `422`. |
| `POST /api/simulations/{run_id}/content/{entry_id}/answer` | Required idempotency header; `{expected_version:int>=1, answer:any}` | `200` | `RunResponse` | `400` missing/not-owned run, entry not actionable/not question, or invalid answer; `409` stale version/key conflict; `401`; `422`. |
| `POST /api/simulations/{run_id}/content/{entry_id}/acknowledge` | Required idempotency header; `{expected_version:int>=1}` | `200` | `RunResponse` | `400` missing/not-owned run or entry not an actionable required fragment; `409` stale version/key conflict; `401`; `422`. |
| `POST /api/simulations/{run_id}/submit` | `{expected_version:int>=1}` | `200` | `RunResponse` | `404` missing/not owned (including service lifecycle error mapping); `409` stale version; `401`; `422`. Re-submitting a non-active owned run returns its current `200` representation. |

`CompleteTurnRequest` contains `expected_version`; `allocation {development, unit_testing,
bug_fixing, integration_testing}` where each is 0..100; `hires[] {employee_type_code:string,
count:int>0}`; `dismiss_employee_ids[]`; and nonnegative overtime, meeting, and training hours
per employee (the three hour fields default to zero). Domain allocation/staffing rules can add
`400` constraints beyond this transport schema.

### Response projections

`RunSummaryResponse` is `{id, scenario_revision_id, class_id|null, status, current_week,
version, started_at, finished_at|null}`. `RunResponse` adds `{engine_version, scenario_title,
scenario_briefing, state, employee_types, final_result|null, deliveries, presentation}`.

`TurnResponse` is `{run:RunResponse, week_number, events[], replayed:boolean}`.
`TurnHistoryResponse` is `{week_number, decision, events, resulting_state, submitted_at,
deliveries[]}`. Student state removes undiscovered bug/specification facts, and student events
remove hidden creation events. Do not infer professor facts from missing properties.

A delivery is `{id, sequence_entry_id, sequence_ordinal, kind, status, checkpoint, title|null,
body|null, prompt|null, question|null, required, latest_response|null, feedback|null, visible,
label|null}`. A question is `{answer_schema, options:[{id,label}],
short_text_max_length|null}`. Latest response is `{command_kind,response_version,value,
answered_at}`. Presentation is `{messages[], visible_fragment_ids[], visible_question_ids[],
flags, theme|null}`. Only delivered, non-professor definitions appear. Definition snapshots,
digests, replay metadata, hidden facts, and professor-only entries never do.

### Run workflow examples

```http
POST /api/simulations
Content-Type: application/json

{"scenario_revision_id":"rev_opaque","class_id":"cls_opaque","seed":12345}
```

Keep the returned `version` and use the `employee_types` projection to construct decisions:

```http
POST /api/simulations/run_opaque/turns
Idempotency-Key: turn-run_opaque-week-1-client-random
Content-Type: application/json

{
  "expected_version": 1,
  "allocation": {"development":55,"unit_testing":20,"bug_fixing":15,"integration_testing":10},
  "hires":[{"employee_type_code":"developer","count":1}],
  "dismiss_employee_ids":[],
  "overtime_hours_per_employee":0,
  "meeting_hours_per_employee":1,
  "training_hours_per_employee":0
}
```

At canonical checkpoints `run_started`, `before_week:N`, `after_week:N`, and `run_finished`,
authored deliveries can become visible/actionable. A required `before_week:N` delivery blocks
week N. `after_week:N` deliveries associate with that persisted turn; `run_started` and
`before_week:N` deliveries have no turn, and `run_finished` deliveries are unassociated unless
the engine reached the terminal checkpoint through a turn. Questions must be answered exactly
once; acknowledgements apply only to required fragments and cannot bypass a question.

```http
POST /api/simulations/run_opaque/content/entry_opaque/answer
Idempotency-Key: content-answer-client-random
Content-Type: application/json

{"expected_version":2,"answer":{"option_id":"quality"}}
```

```http
POST /api/simulations/run_opaque/content/fragment_opaque/acknowledge
Idempotency-Key: content-ack-client-random
Content-Type: application/json

{"expected_version":3}
```

Authored answers are learning interactions, never score contributions. Supported effects alter
presentation only (`show_message`, flags, and themes). Each successful content command increments
the run version.

```http
POST /api/simulations/run_opaque/submit
Content-Type: application/json

{"expected_version":8}

HTTP/1.1 200 OK
{"id":"run_opaque","status":"submitted","version":9,"finished_at":"2026-08-13T12:00:00Z","final_result":{"outcome":"submitted","score":74.5},"...":"RunResponse fields omitted"}
```

Submission finalizes and scores an active run, resolves terminal authored content, and increments
the version. Runs may also finish through engine outcomes during a weekly turn.

### Optimistic concurrency and idempotency

`version` is a monotonically increasing revision of the mutable run projection. Send the last
read value as `expected_version` on turns, answers, acknowledgements, and submission. A successful
mutation changes it to `expected_version + 1`. On concurrent-version `409`, fetch the run again,
show the changed state, reconstruct/review the user's intent, and send a new command using the
new version.

Turns and content commands additionally require a client-generated idempotency key scoped to
the run and command store. Generate it once per user intent and retain the same key and exact
logical request across timeout/connection retries. The server hashes a canonical request. For
turns, hires with the same type are combined/sorted and dismissed IDs are deduplicated/sorted;
for content, command kind, entry, expected version, and normalized answer (including stable
multi-choice ordering) participate. An identical retry returns the committed result without
applying another turn/response/effect (`TurnResponse.replayed` exposes this for turns).

Safe retry after a lost response:

```text
key = turn-run_opaque-week-2-7f...; expected_version = 4; decision = D
timeout -> resend the same key, version, and D -> original committed turn is replayed
```

Conflicting reuse:

```text
key = content-answer-9a... with answer {"option_id":"quality"}
reuse same key with {"option_id":"speed"} -> 409 idempotency conflict
```

Do not solve an idempotency conflict by blindly changing keys: determine whether the earlier
command committed, refetch, and obtain/review current intent. Submission has optimistic
concurrency but no idempotency header; submitting an already terminal owned run is naturally a
read-like `200` return.

## Professor results and administrative audit

All routes are professor-only and ownership-scoped.

| Method/path | Input | Success | Response schema | Meaningful endpoint errors |
| --- | --- | --- | --- | --- |
| `GET /api/classes/{class_id}/results` | Class path ID | `200` | `ClassResultResponse[]` | `404` class missing/not owned; auth/`422`. |
| `GET /api/classes/{class_id}/results/{run_id}` | Class and run path IDs | `200` | `RunAuditResponse` | `404` class/run missing, mismatched, or not owned; auth/`422`. |
| `GET /api/audit` | Query `limit:int=50` (1..200), `offset:int=0` (>=0) | `200` | `AuditResponse[]` | Auth/`422`. |

`ClassResultResponse` is `{run_id, student_id, student_username, class_name, scenario_name,
scenario_revision_id, status, current_week, finished_at|null, final_result|null}`.
`RunAuditResponse` adds `{seed, engine_version, current_state, turns, content_audit}`. Each audit
turn is `{week_number, turn_seed, decision, resulting_state, events, submitted_at}`. Unlike the
student projection, this state/event history may contain intentionally hidden facts.

```http
GET /api/classes/cls_opaque/results

HTTP/1.1 200 OK
[{"run_id":"run_opaque","student_id":"usr_opaque","student_username":"student.one","class_name":"Section A (sanitized)","scenario_name":"Sanitized onboarding scenario","scenario_revision_id":"rev_opaque","status":"submitted","current_week":4,"finished_at":"2026-08-13T12:00:00Z","final_result":{"outcome":"submitted","score":74.5}}]
```

```http
GET /api/classes/cls_opaque/results/run_opaque

HTTP/1.1 200 OK
{
  "run_id":"run_opaque",
  "student_id":"usr_opaque",
  "student_username":"student.one",
  "class_name":"Section A (sanitized)",
  "scenario_name":"Sanitized onboarding scenario",
  "scenario_revision_id":"rev_opaque",
  "status":"submitted",
  "current_week":4,
  "finished_at":"2026-08-13T12:00:00Z",
  "final_result":{"outcome":"submitted","score":74.5},
  "seed":12345,
  "engine_version":"1",
  "current_state":{"week":4,"budget":42000,"...":"full professor projection"},
  "turns":[{"week_number":1,"turn_seed":12345,"decision":{"...":"sanitized"},"resulting_state":{"...":"full state"},"events":[],"submitted_at":"2026-08-13T11:15:00Z"}],
  "content_audit":{"deliveries":[],"responses":[],"effects":[],"digest_status":"verified","divergences":[]}
}
```

`AuditResponse` is `{id, action, target_type, target_id, details, created_at}`. Content audit
contains immutable deliveries (`id`, entry ID/ordinal, checkpoint, visibility,
`hidden_from_students`, definition digest/snapshot, status/times, optional turn ID/week), authored
responses (entry, response version, command kind, normalized answer, answer time, request digest,
one-way idempotency-key digest), effects (entry/index/payload, before/after projection digests,
time, optional turn), and replay verification. `digest_status` is `verified` or `diverged`;
divergences contain `{category, record, expected, actual}`. Replay is read-only and never
synthesizes historical records. Digests cover canonical student presentation, not simulation
state or score.

```http
GET /api/audit?limit=2&offset=0

HTTP/1.1 200 OK
[{"id":"audit_opaque","action":"class.created","target_type":"class","target_id":"cls_opaque","details":{"name":"Section A (sanitized)"},"created_at":"2026-08-13T10:30:00Z"}]
```

## Field-level semantics

* **Opaque identifiers** (`id`, `*_id`, membership/assignment/delivery/entry IDs) are persistence
  identities. Store and echo them exactly; never parse, sort semantically, or substitute a
  display name. A revision ID is globally referential; its `revision_number` is only meaningful
  within one scenario.
* **Timestamps** are JSON ISO-8601 date-times. They are server-generated instants; accept an
  offset or `Z`, parse as timezone-aware, and do not use client clocks to order mutations.
  Nullable published/finished/completed/turn fields mean that lifecycle point has not occurred
  or no turn association exists.
* **Revision numbers/schema versions/run versions/response versions** are distinct. Scenario
  `revision_number` orders immutable author revisions; `schema_version` selects definition
  format; run `version` is optimistic concurrency; content `response_version` versions the
  recorded response (currently the first response is 1).
* **Digests** are deterministic integrity/replay values, not source data, identifiers, secrets,
  or scores. Definition/request/projection digests cover different canonical payloads. The
  idempotency-key digest is one-way; the raw key is not disclosed in professor audit.
* **Statuses** are lifecycle values emitted by the service (for example draft/published,
  active/submitted/engine terminal outcomes, and actionable/completed delivery states). Treat
  unknown future values as valid strings and gate actions using documented lifecycle behavior.
* **Authored checkpoints** are canonical strings: `run_started`, `before_week:N`,
  `after_week:N`, `run_finished`. Sequence ordinal fixes authored ordering. Delivery status and
  `required` determine whether action is needed; visibility and `hidden_from_students` control
  disclosure, not scoring.
* **Simulation projections** are audience-specific snapshots. `RunResponse.state` and turn
  events are filtered for students; result audit exposes full state. `employee_types` is copied
  from the pinned scenario revision. `presentation` is independently derived authored UI state.
  `final_result` is null until a terminal outcome/submission and must not be recomputed client-side.

## Repeatable router/schema reconciliation

Perform this checklist in every change that touches decorators, dependencies, request/response
models, or service-to-HTTP exception mappings under `app/api/`:

1. Start from a clean environment, run the API with the intended settings/database, and save
   its schema: `curl -fsS http://127.0.0.1:8000/openapi.json > /tmp/pm-sim-openapi.json`.
2. Inventory decorators without relying on this guide:
   `rg -n '^@(?:app|router)\.(get|post|put|patch|delete)' backend/app/api backend/app/main.py`.
   Compare every method and fully mounted path (router prefix plus `/api`) with every row above.
3. Inspect dependencies (`CurrentUser`/`ProfessorUser`), `status_code`, `response_model`, body
   models, `Path`/`Query`/`Header` constraints, and every caught `HTTPException`. Update role,
   input, success, response, and error columns together.
4. Diff the generated contract against the reviewed baseline, for example
   `git diff --no-index backend/docs/openapi-baseline.json /tmp/pm-sim-openapi.json` if the team
   maintains one, or inspect paths/components with `jq '.paths, .components.schemas'`.
5. Exercise at least one success plus authentication, authorization, validation, missing-resource,
   lifecycle, stale-version, identical-retry, and conflicting-key cases affected by the change.
   Redact cookies, passwords, names, and IDs before updating examples.
6. Search model names and endpoint paths in this file, update workflows/field notes as well as
   tables, render Markdown, and have the reviewer explicitly compare the decorator/model diff
   with the documentation diff. A decorator or Pydantic model change is incomplete without the
   corresponding guide update (or a written explanation that it is internal-only).

## Related documentation

* [Frontend API integration](../../frontend/docs/api-integration.md)
* [Frontend authentication](../../frontend/docs/authentication.md)
* [Authored scenario content](authored-content.md)
