# Criteria v-aq-front-02 (hidden from the candidate)

Functional

- G01 The api layer throws a typed error that carries the numeric status; all four request helpers use it (the message may stay human-readable).
- G02 Consumers test the status through one helper or type guard (for example "is not found"), not through the message; the repeated retry/refetch predicates are written once and reused by the live and the historical query.
- G03 The page's "no data yet" decision uses the same guard.
- G04 Redirect-in-flight error handling is unchanged.
- G05 Tests: the typed error carries 404/401/500; the retry predicate returns false for 404 and true otherwise; the page still shows the empty health view on 404 and the failure text on 500.
- G06 No behaviour change for users; no new dependency.

Rules checked: CODE.4 (a repeated expression becomes one function), CODE.2 (failures stay visible), CODE.3 (names say what they are for; no boolean flag parameter added), T.3, DEL.3 (one thing).

Hard gates

- Typecheck, lint and tests pass (T.1).
- No `message.includes(` on an API error remains in non-test code.

Regressions

- Retrying on 404 or no longer retrying on 500.
- Swallowing the status in the helper that hides the error from the query layer.
