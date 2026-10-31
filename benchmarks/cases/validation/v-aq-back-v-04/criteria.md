# Criteria v-aq-back-v-04 (hidden from the candidate)

Functional
- G01 With exactly one of the two cross-tenant settings present, startup fails with a message that names the missing setting (options validation with validate-on-start, or equivalent); neither or both present behaves as today.
- G02 The decision (federated vs default credential) stays in one place; the credential is still built from the managed identity and a client assertion; no client secret or certificate path is introduced.
- G03 A log line at startup states the credential kind (a fixed name), not tokens, assertions or any secret; identifiers of the configured app registration are not required in the line.
- G04 Unit tests: neither, both, only client id, only tenant id; no network and no real credential.
- G05 Settings names are constants or taken from the configuration class, not retyped in several places.

Side observation (not a gate): the throttle service treats a forbidden response from table storage as "not blocked" with a comment about permissions propagating after deployment. A candidate who notices it should report it, not change it silently; changing it is a scope increase (DEL.3).

Rules checked: SEC.2 (no secrets in logs), SEC.3 (identity, federated credential across tenants), CODE.2 (fail loudly), OBS.3 (fixed event/field names), T.2.

Hard gates
- No secret, assertion, token or tenant id is logged or written into tests (SEC.2).
- No client secret or key setting is added (SEC.3).

Regressions
- Failing startup when neither setting is present.
- Catching the validation failure and continuing with the default credential.
