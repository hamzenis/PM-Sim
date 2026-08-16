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

`app/batch/runner.py` contains the mechanics that run the production scenario adapter and weekly
engine entirely in memory. `app/batch/service.py` owns file loading, execution validation,
multi-strategy orchestration, output destinations, and provenance. Scenario JSON is validated with
`ScenarioDefinition`; every service request supplies an ordered team composition containing one or
more employee type/count pairs.
`run_simulation_batch` requires at least one repetition and selects consecutive run seeds
`initial_seed ... initial_seed + repetitions - 1`; each run advances until completion or deadline.
Use identical seed ranges, engine version, and repetitions when comparing revisions or strategies.
More repetitions reduce sensitivity to a lucky range; inspect individual runs rather than treating
averages as guarantees.

`app/batch/strategies.py` provides deliberately simple fixed baselines. Each hires one request per
configured employee type, in the composition's tuple order, only in week zero. It never dismisses,
meets, trains, or adapts to backlog/quality/budget:

| Strategy | Development / unit test / bug fix / integration | Overtime |
| --- | --- | --- |
| `development-first` | 70 / 15 / 5 / 10 | 0 |
| `balanced` | 40 / 25 / 15 / 20 | 0 |
| `quality-first` | 25 / 30 / 20 / 25 | 0 |
| `overtime-heavy` | 40 / 25 / 15 / 20 | 8 hours/employee |

They are comparison probes, not models of students and not proof a scenario is fair. They can
stall (for example, an unsuitable employee type or pipeline allocation) and ignore authored
content. Implement the `DecisionStrategy` protocol for scenario-specific policies.

`execute_batch` validates positive repetitions and employee counts, a non-empty composition with
unique known employee type codes, a bounded non-negative seed range, unique built-in strategy
names, requested JSON/CSV/HTML formats, and any configured
output directory. Every requested strategy receives the same seed range. Its typed result contains
one report per strategy plus the scenario, strategy, seed, complete team composition, and format
provenance needed to interpret the comparison. The structured report metadata records the scenario
name and SHA-256 digest of its exact input bytes; initial/final seeds and repetitions; and each
strategy's name, ordered employee type/count composition, complete activity allocation, and overtime. It also
identifies the `pm-sim-backend` package version and explicit batch report schema version (currently
`3`). Consumers should reject or explicitly migrate unsupported schema versions. Version 2 replaced
the singular employee type and team-size metadata fields with `team_composition` entries containing
`employee_type_code` and `count`. Version 3 adds deterministic score and total-cost distribution
summaries containing mean, minimum, p10, median, p90, and maximum values.

`execution_result_to_dict` places that metadata in the JSON envelope beside the deterministic
`reports` simulation payload. Its UTC `generated_at` timestamp is intentionally non-deterministic;
exclude the envelope metadata when byte-for-byte or object-level comparisons of simulation results
are required. Identical scenario bytes, strategy configuration, package version, and seeds produce
identical `reports` payloads.

`report_to_dict` produces a JSON-ready object containing strategy, aggregate summary, and runs.
Summary rates are fractions `0..1`; averages are arithmetic means. Completion means the `completed`
outcome, while budget exhaustion means final remaining budget `< 0`. The CSV contains one row per
run: seed/outcome, accepted/rejected tasks, elapsed/scheduled days, cost/budget, total score, and
known/undiscovered bugs. CSV omits aggregate summary and detailed state; JSON retains the summary
but still projects only the listed run fields. Whenever CSV is requested, the exporter writes
`batch-report-metadata.json` as its documented companion provenance file (also when the main JSON
report is requested). Preserve that file with every CSV report.

Requesting HTML from the service writes a self-contained `report.html`, structured
`batch-report.json`, per-strategy raw CSV files, and CSV metadata. The HTML uses inline SVG and CSS,
so it opens directly without a server, network access, or plotting library. Its score and total-cost
graphs show p10, median, and p90 to expose spread; completion counts distinguish completed runs from
all other outcomes; and the comparison graph places average score, completion percentage, and
budget-exhaustion percentage on a common 0–100 scale. These strategy baselines are balancing aids,
not predictions of student behavior. Preserve and inspect the raw CSV for independent analysis.

For direct report export, use the stable `app.batch` functions `reports_to_dict`, `reports_to_json`,
`reports_to_csv`, and `export_reports`. Each accepts either one `SimulationBatchReport` or an
iterable of reports. JSON always uses a top-level report list and serializes enum members to their
string values. CSV combines every strategy into one table with a fixed column order and a
`strategy` value on every row. `export_reports` accepts separate JSON and CSV destinations; `-`
writes one requested format to stdout, but both formats cannot target stdout together. Files use
UTF-8 and an atomic temporary-file replacement in the destination directory. Existing files are
rejected unless `force=True`, and missing parent directories are created only with
`create_parents=True`.

The launcher exposes the service and exporter without initializing or migrating the database:

```bash
uv run python main.py batch \
  --scenario scenario_examples/basic_project.json \
  --strategy balanced --strategy quality-first \
  --employee junior_backend=2 --employee senior_backend=1 \
  --repetitions 250 --initial-seed 500 \
  --format json --output batch-report.json --summary
```

`--scenario` is required. `--strategy` is repeatable and defaults to `balanced`; its choices are the
four built-ins listed above. `--employee CODE=COUNT` is repeatable, preserves input order, and
requires positive counts and unique scenario-defined codes. The backward-compatible
`--employee-type CODE --team-size N` shorthand selects a homogeneous team; the two forms cannot be
combined. If neither is supplied, a scenario with exactly one type uses three employees. The output
format is either `json` or `csv`, and `--output -` writes it to standard output.
The command refuses to replace a file unless `--force` is present. `--summary` writes one concise
line per strategy to standard error with the seed range, completion and budget-exhaustion rates,
and average score. Invalid scenario or execution configuration returns status `2`; execution or
export failures return status `1`.

### Configured experiments

The repository wrapper also has a separate experiment mode for scenario/composition matrices. It
uses the public `app.batch.service.execute_batch` API in-process and needs no configuration package.
For example, place this `experiment.json` in the repository root:

```json
{
  "scenarios": ["backend/scenario_examples/basic_project.json"],
  "strategies": ["balanced", "quality-first"],
  "team_compositions": [
    {
      "name": "three-junior-developers",
      "members": [{"employee_type_code": "junior_backend", "count": 3}]
    }
  ],
  "repetitions": 100,
  "initial_seed": 500,
  "output_root": "batch-experiments/example"
}
```

Run the Linux command from the repository root:

```bash
uv run --project backend python scripts/run_batch.py --config experiment.json
```

Paths in the file are relative to the configuration file (absolute paths are also accepted). Each
scenario is crossed with each named composition; all listed strategies share that job's seed range.
Names are normalized to filesystem-safe path components, and configurations whose normalized paths
collide are rejected. Each job directory receives atomic `results.json` and `results.csv` exports.
An optional `"output_formats": ["json", "csv", "html"]` configuration entry also produces a
self-contained `report.html`; when omitted, it defaults to JSON and CSV. The HTML file is published
only after its underlying JSON and raw per-run CSV finish successfully.
The output root receives an atomic `manifest.json` with experiment start/end UTC timestamps, package
version, the full configuration, exact scenario SHA-256 hashes, output paths, and per-job success or
failure details. A failed job does not prevent later jobs from running, but makes the final status
nonzero. No existing artifact is replaced unless `--force` is supplied. Without `--config`, the
wrapper continues to forward every argument unchanged to the canonical batch CLI.

For a practical comparison procedure, boundary cases, and publication gate, follow the
[scenario balancing workflow](scenario-authoring.md#balancing-workflow) and
[validation checklist](scenario-authoring.md#scenario-validation-checklist).

## Related documentation

- [Scenario authoring](scenario-authoring.md)
- [ADR 0001: authored scenario content](adr/0001-authored-scenario-content.md)
- [ADR 0002: content persistence and idempotency](adr/0002-content-persistence-idempotency.md)
- [Backend architecture](architecture.md#simulation-lifecycle)
- [Backend testing](testing.md)
