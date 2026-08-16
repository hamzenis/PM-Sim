# KT-1571220 balancing evidence (2026-08-13)

This directory is the pre-publication professor-review record for the revised data-warehouse
migration scenario. It does **not** represent a published immutable revision. The generator uses
the shared validated scenario loader, batch service, provenance model, distribution summary
extension, and atomic export layer. `batch-summary.json` records the scenario SHA-256,
strategy definitions, aggregate metrics, score distributions, and component ranges;
`batch-runs.csv` retains every run for outlier review.

## Controlled calibration sequence

Only one numeric parameter group was changed between each exploratory comparison:

1. **Employee statistics:** throughput was raised while preserving the relative role profiles;
   the final values are 1.7 times the prior values (rounded to two decimals). Senior engineer and
   architect day rates were then set to EUR 1,000 and EUR 1,300 so the senior-heavy roster buys
   schedule certainty at a visible risk to the effective EUR 210,000 ceiling.
2. **Workload/difficulty:** total workload was reduced from 120 to 100 after mixed four-person
   rosters still could not clear the pipeline. The 30/45/25 difficulty mix was retained.
3. **Budget/deadline:** the nominal EUR 240,000 and 70 working-day values were retained so the
   authored EUR 30,000 contingency shock remains internally consistent. Evidence separately
   reports breach of the effective EUR 210,000 ceiling.
4. **Rules:** all stress, recovery, training, and familiarity values were retained. Runs first use
   temporary `none`, then restore intended `semi` randomness. Both modes use seeds 1,571,220–
   1,571,419 for every strategy. `none` removes output variance, but seeded defect/specification
   draws still vary, so it is not expected to collapse every row to one result.
5. **Scoring:** the requested 45/35/20 budget/quality/time weights and exponents were retained for
   review rather than silently changing the educational priority.

## Final comparison

The intended `semi` batch contains 200 repetitions per strategy. Completion rates are 100% for
senior-heavy, 81.5% for two-hours-per-person recovery overtime, 75% for quality-first, and 62.5%
for specialist-balanced staffing. These are multiple viable approaches with materially different
cost/schedule trade-offs. The overtime probe is deliberately moderate and starts after week 4.
Low-cost staffing completes 0% and averages 62.92 accepted / 37.08 rejected tasks; development-first
completes 1% and averages 86.685 accepted / 13.315 rejected tasks. Weak choices therefore have
visible delivery consequences without making the reasonable mixed strategies depend on lucky
seeds.

Senior-heavy delivery averages EUR 218,225 and breaches the effective ceiling in 68.5% of runs,
while specialist-balanced, quality-first, and overtime-recovery average EUR 201,798, EUR 191,823.75,
and EUR 185,827. Senior-heavy exhausts the nominal EUR 240,000 budget in 13% of `semi` runs; none
of the other strategies exhausts it. Mean elapsed time is 50.75, 66.6, 66.375, and 64.3 working
days respectively for those four viable approaches.

## Scoring review and publication warning

The evidence confirms that quality is not wholly irrelevant: the quality component ranges from
11–35 and weak strategies receive lower total-score distributions. Budget also affects the costly
senior-heavy outliers. However, the time component is exactly 20 for **every** saved run, because
the current result formula awards full time points whenever elapsed days are at or below the
scheduled deadline, and the engine stops at that deadline. The 45/35/20 configuration therefore
cannot make schedule score-sensitive through scenario numeric changes alone. Total scores are also
compressed near 100 for approaches that nearly finish under the nominal budget.

Professor review should consider completion rate, elapsed days, effective-ceiling breaches, and
accepted/rejected scope alongside total score. Do not publish a new immutable revision on the
assumption that total score captures schedule trade-offs; correcting that limitation requires a
separate engine/scoring design change, followed by regeneration of this evidence with identical
seeds.

## Reproduce

From `backend/` (module execution keeps the backend package configured without modifying
`sys.path`):

```bash
uv run python -m \
  scenario_examples.balancing.datawarehouse_migration_kt_1571220.generate_evidence
```

The JSON and CSV artifact schemas are unchanged by the batch-service migration. Regeneration only
updates their data and records the shared service entry point; generated artifacts are reviewed
separately and are not updated for code-only refactors.
