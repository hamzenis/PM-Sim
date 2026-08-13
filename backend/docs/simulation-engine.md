# Simulation engine

This is the behavioral reference for authors and maintainers. The pure modules under
`app/simulation/` operate on immutable value objects and do not import HTTP or persistence code.
`app/scenarios/to_simulation.py` maps a validated, pinned scenario revision into engine inputs;
`app/simulations/service.py` persists runs and turns.

## Units, state, and deterministic randomness

* Time is in working days and staff-hours. Throughput is tasks per **eight productive hours**;
  allocations are percentages totaling 100. Money uses the scenario's consistent currency unit.
* Tasks are anonymous integer pools (`easy`, `medium`, `hard`). `app/simulation/models.py` enforces
  non-negative counts and the containment invariants completed ⊇ unit-tested ⊇ integrated, with
  known and undiscovered defects confined to eligible pools.
* `app/simulation/tasks.py` creates initial pools using largest remainders: floor each exact share,
  then award remaining tasks by descending fractional remainder, breaking ties easy, medium, hard.
* `app/simulation/randomness.py` owns randomness. `SeededRandomSource` wraps NumPy's seeded generator;
  `RecordedRandomSource` supplies exact test draws. Identical engine version, revision, starting
  state, decision, and random stream reproduce a turn. Batch runs intentionally construct seed
  `run_seed + state.week` for each week; replay through the same entry point rather than assuming
  random draws remain compatible after an engine change.

`app/simulation/engine.py` initializes week and elapsed days to zero, budget to the project budget,
all tasks in the deterministic backlog, all other pools empty, and no employees.

## Weekly turn order

`app/simulation/turn.py` is the orchestration authority. A turn refuses to run at zero remaining
days and performs these steps in order:

1. apply dismissals and hires;
2. calculate this turn's capacity and reserve meetings/training;
3. unit test previously completed work and discover bugs;
4. fix already-known bugs;
5. develop backlog tasks, creating hidden bugs/specification failures;
6. integration test clean unit-tested work, returning specification failures to backlog;
7. update employee dynamics;
8. charge staff cost, advance week/days, then evaluate completion/deadline.

The order matters: work developed this week cannot be unit tested until a later turn, but work
tested and fixed early in the turn can become eligible for integration later in that same turn.
Events report each transition in this same order.

## Capacity and staffing

`app/simulation/models.py` and `app/simulation/capacity.py` define capacity as
`employees × working_days × hours_per_day + employees × overtime_hours_per_employee`, bounded at
zero. The final week uses the lesser of days per week and remaining days. Meeting and training
hours are `team size × per-employee hours` and are reserved before the four activity percentages
divide the remainder. Negative reservations and reservations over total capacity fail; capacity is
never silently overbooked. Calculations retain floating-point hours without display rounding.

`app/simulation/staffing.py` validates employee types, dismissal IDs, and generated unique employee
IDs. Dismissals occur before additions. New employees start with motivation `.75`, stress `.10`,
experience `0`, familiarity `0` (`app/simulation/models.py`). All employees present after staffing
are charged `cost_per_day × working_days`; overtime, meetings, training, and hiring have no separate
cost. Cost is a float and is not rounded by the engine.

## Productivity and task progression

`app/simulation/productivity.py` spreads each activity's team-hours across the eligible difficulty
pool in proportion to its remaining counts, then equally across employees. Per difficulty, base
output is `(difficulty hours / 8) × employee-type throughput`. It is multiplied by experience
(`1 + experience`) and combined employee/team efficiency:

* member efficiency averages familiarity, motivation, and proximity to ideal stress `.2`, clamped
  to `[0,1]`;
* team efficiency uses the communication-channel curve and is capped at `1`;
* the two efficiencies are averaged.

Expected fractional output becomes discrete in `realize_task_output`: `none` rounds half up;
`full` takes a Poisson draw; `semi` rounds half up the average of expectation and its Poisson draw.
Every result is capped by the available integer pool. The same mechanism sizes development, unit
testing, bug fixing, and integration testing.

`app/simulation/testing.py` reveals defects by sampling without replacement from eligible untested
tasks; fixes can select known bugs only. `app/simulation/integration.py` accepts clean unit-tested
tasks, samples latent specification failures, and returns failures to the backlog while removing
their completed/tested/specification markers. Integer pool bounds prevent completing or testing
more work than exists.

## Quality

`app/simulation/quality.py` calculates bug probability per difficulty as a throughput-weighted team
average of `(employee-type error_rate + employee stress) / 3`, clamped to `[0,1]`. Specification
failure probability is one minus management quality; management skill is weighted by employee
experience and motivation and clamped before inversion. Each newly developed task receives
independent seeded probability draws for both hidden properties. Bugs remain undiscovered until
unit testing; specification failures are exposed at integration. Sampling functions return integer
counts and never exceed their source pools.

## Employee dynamics

`app/simulation/employee_dynamics.py` updates after work. Positive overtime raises stress and lowers
motivation per hour; every turn subtracts weekend stress recovery; a one-person team adds solo
stress. Meetings increase familiarity per employee-hour. Training benefits only employees below
the team's average effective throughput: experience gains scale with the performance gap and
training hours, with diminishing returns from existing experience, and motivation receives the
configured hourly boost. Stress, motivation, and familiarity are clamped to `[0,1]`; experience is
non-negative but uncapped. With no employees the update is a no-op.

## Budget, completion, and results

Budget does **not** stop a run. `app/simulation/staffing.py` computes salary and
`app/simulation/turn.py` subtracts it after work, so remaining budget may become negative. The
engine stops automatically when either all original tasks are integration-tested (`completed`) or
remaining working days reaches zero (`deadline_reached`); explicit submission produces
`submitted`. In `app/simulation/results.py`, completion takes precedence over submission, which
takes precedence over deadline.

`app/simulation/results.py` derives accepted tasks from the integrated pool, rejected tasks as
original total minus accepted, total cost as initial minus remaining budget, and scheduled days as
elapsed plus remaining. Quality points truncate the bounded accepted ratio raised to its exponent.
Time and budget receive their full component limit at or below the target; beyond it, their points
decline from the percentage over target raised to the exponent, bottoming at zero. Those components
use Python `round`; overall score is the rounded percentage of the three configured limits (or zero
if all limits are zero). Scores measure the current/final state even for submission or deadline.

## Batch analysis

`app/batch/runner.py` runs the production scenario adapter and weekly engine entirely in memory.
`run_simulation_batch` requires at least one repetition and selects consecutive run seeds
`initial_seed ... initial_seed + repetitions - 1`; each run advances until completion or deadline.
Use identical seed ranges, engine version, and repetitions when comparing revisions or strategies.
More repetitions reduce sensitivity to a lucky range; inspect individual runs rather than treating
averages as guarantees.

`app/batch/strategies.py` provides deliberately simple fixed baselines. Each hires one employee type
only in week zero, never dismisses, meets, or trains, and never adapts to backlog/quality/budget:

| Strategy | Development / unit test / bug fix / integration | Overtime |
| --- | --- | --- |
| `development-first` | 70 / 15 / 5 / 10 | 0 |
| `balanced` | 40 / 25 / 15 / 20 | 0 |
| `quality-first` | 25 / 30 / 20 / 25 | 0 |
| `overtime-heavy` | 40 / 25 / 15 / 20 | 8 hours/employee |

They are comparison probes, not models of students and not proof a scenario is fair. They can
stall (for example, an unsuitable employee type or pipeline allocation) and ignore authored
content. Implement the `DecisionStrategy` protocol for scenario-specific policies.

`report_to_dict` produces a JSON-ready object containing strategy, aggregate summary, and runs.
Summary rates are fractions `0..1`; averages are arithmetic means. Completion means the `completed`
outcome, while budget exhaustion means final remaining budget `< 0`. The CSV contains one row per
run: seed/outcome, accepted/rejected tasks, elapsed/scheduled days, cost/budget, total score, and
known/undiscovered bugs. CSV omits aggregate summary and detailed state; JSON retains the summary
but still projects only the listed run fields. Keep scenario revision and engine version beside an
export because neither format embeds them.

For a practical comparison procedure, boundary cases, and publication gate, follow the
[scenario balancing workflow](scenario-authoring.md#balancing-workflow) and
[validation checklist](scenario-authoring.md#scenario-validation-checklist).

## Related documentation

- [Scenario authoring](scenario-authoring.md)
- [ADR 0001: authored scenario content](adr/0001-authored-scenario-content.md)
- [ADR 0002: content persistence and idempotency](adr/0002-content-persistence-idempotency.md)
- [Backend architecture](architecture.md#simulation-lifecycle)
- [Backend testing](testing.md)
