# Criteria v-aq-back-v-03 (hidden from the candidate)

Functional
- G01 The clock comes in through the constructor (TimeProvider or an equivalent abstraction) in the throttle service; no direct wall-clock read remains in it.
- G02 The composition root registers the real clock once; services do not construct it.
- G03 The window arithmetic (current window start, next window, remaining wait, block expiry) is separable from the table I/O, or the table client is replaced by a fake, so a test can set the instant.
- G04 Tests: rollover at a minute/30 second boundary, a block that expires exactly now, a block still active, count at the limit. All run in milliseconds with no sleeping.
- G05 Observable behaviour is identical at the boundaries (window start alignment, the "< limit" comparison, the delay computed).
- G06 The same treatment is applied to the load-state and cadence services only if the change stays small and one thing; otherwise listed as follow-up in the PR text (DEL.3).

Rules checked: T.2 (clock in through DI), CODE.8 (interface and one composition root), T.3 (tests run in their layer), DEL.3 (one thing, evidence shown).

Hard gates
- Build green, existing tests pass (T.1).
- The orchestrators keep using the durable context's time, not the new clock (otherwise replay breaks). A change to an orchestrator is a failure.

Regressions
- Behaviour change in the handling of a missing entity or of the forbidden status; those are out of scope and must keep their current behaviour (the candidate may raise them as a note).
- Introducing a static clock or ambient context.
