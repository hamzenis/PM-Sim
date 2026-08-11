# ADR 0002: Authored-content persistence and legacy idempotency

Authored-content deliveries, responses, and presentation effects are persisted only when
they occur after this schema is deployed. The migration does not infer these facts for
historical runs.

`simulation_turns.request_digest` is nullable specifically to identify a legacy turn whose
complete canonical request was never stored. Idempotency handling may continue to match such
a turn by its existing run-scoped idempotency key, but it must not claim that the request was
digest-verified. A retry that requires payload equivalence must be rejected (or handled through
an explicit legacy-conflict path) when the matched turn has a null digest. New turns must store
the digest calculated from the complete canonical request. No sentinel or digest synthesized
from the historical decision subset is valid.

Content response records preserve every accepted response version. Their run-scoped
idempotency key identifies a retry, while the canonical request digest verifies that the retry
represents the same request.
