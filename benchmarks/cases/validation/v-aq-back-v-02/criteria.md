# Criteria v-aq-back-v-02 (hidden from the candidate)

Functional
- G01 A server error (HTTP 5xx other than the one tolerated case below) from the resource health and the service health endpoints is not turned into an empty list; it propagates to the activity.
- G02 The activity fails (or reports a failed result the orchestration acts on) so that the per-subscription, per-dataset checkpoint is not advanced for that run.
- G03 The one documented tolerated case stays: the "provider not registered" conflict (409) still returns an empty list with a warning. If the candidate also keeps 500 as tolerated, that is a failure of G01.
- G04 The failure is logged once, with the subscription id and dataset key but no payload; a named metric records it.
- G05 A test with a stub handler shows 500 now surfaces and 409 still returns empty (T.4: the escaped defect gets a test at the layer where it lives).
- G06 Throttling (429/503) behaviour is unchanged.

Rules checked: CODE.2 (a failed response is checked, not ignored; the exception is handled where something useful can be done), OBS.3 (stable names, identifiers, no content), T.4, T.2.

Hard gates
- The checkpoint does not advance when the endpoint returns a server error (functional proof by test).
- The build is green and existing tests pass (T.1).

Regressions
- Removing the catch for the tolerated conflict.
- Retrying 5xx in a loop inside the service (the design hands throttling to the orchestrator).
- Swallowing the failure at the orchestration level.
