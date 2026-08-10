# Legacy simulation behavioral inventory

This document records behavior observed in the Django implementation. It is evidence for
parity work, not a claim that every legacy behavior is desirable.

## Weekly execution order

1. Apply hires and dismissals.
2. Reserve a complete day for a team event and another complete day for integration testing.
3. For each remaining day, charge daily staff cost, reduce weekend stress, run meetings,
   run training, apply overtime and solo-worker stress, then perform task work.
4. Within each member's task work, unit test first, fix known bugs second, and develop new
   tasks with the remaining capacity.
5. Run integration testing on its reserved day. Incorrect specifications return to todo.
6. Run the team event on its reserved day.

## Characterized formulas

`app.parity.legacy_math` transcribes the formulas without importing Django:

- team communication efficiency;
- member efficiency and Poisson-based capacity;
- motivation and error adjustment by task difficulty;
- bug and specification probabilities;
- meeting distribution;
- overtime/weekend stress;
- training experience gain;
- quality, budget, and time scores.

Golden values are stored in `tests/parity/fixtures`. `app.parity.comparison` compares nested
old/new snapshots and reports exact JSON-style paths.

## Approved simplified rewrite behavior

- Legacy tasks have one scalar throughput plus a development-quality field. The rewrite uses
  easy/medium/hard throughput values.
- Legacy actions are boolean modes sharing each member's daily capacity in a fixed order. The
  rewrite uses student-selected percentage allocation across the whole week.
- Legacy integration testing consumes a complete day regardless of team size. The rewrite
  allocates team hours.
- Legacy weekend reduction runs when the stored day is divisible by five, including day zero.
- Legacy completion capacity scales the Poisson/deterministic value by `0.2` and uses Python
  `round`, including its ties-to-even behavior.
- Legacy accepted tasks do not require integration testing; they require done, bug-free, and
  correct specification. The rewrite currently treats integration-tested tasks as accepted.
- Legacy time/budget scoring truncates the remaining percentage before applying the configured
  limit. The rewrite rounds after scaling.
- Legacy randomness uses both Python's global RNG and NumPy's global RNG. Replaying a run
  requires controlling both streams and stabilizing unordered task-set iteration.

The differences above are approved redesigns and must remain the rewrite behavior. Their
machine-readable decision records are in `docs/approved-redesigns.json`. Legacy formulas stay
available for archaeology and comparison, but parity work must not reintroduce the old scalar
throughput, boolean work modes, reserved integration day, global RNG, or legacy scoring rules.

Any newly discovered difference must still be classified as parity, an approved redesign, or
an unresolved ambiguity before altering the new engine.
