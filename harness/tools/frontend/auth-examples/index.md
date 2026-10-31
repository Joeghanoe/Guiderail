# Auth state producers

`screenshot.mjs --auth-state <file>` captures a page behind a login by seeding browser storage and cookies before the app boots. It
does not log in. A producer is any script that fetches a credential out of band and writes the state file (format in
[`../auth-state.mjs`](../auth-state.mjs)).

* `msal-client-credentials.mjs` - Azure AD / Entra ID with MSAL: client-credentials token, MSAL v5 cache entries in `sessionStorage`. The pattern of
  the Aquarium portal's Cypress login, without Cypress. Not run against a real tenant by the harness.

Other shapes are the same few lines: an app that keeps `{ "token": "..." }` in `localStorage`, a session in `sessionStorage`, or a cookie
from a dev-only token endpoint. Write the state from the values your own test setup already creates; use a synthetic user (SEC.2).

A repo that already has Cypress with a `cy.session` login can also capture with `cy.screenshot`; the harness checks (overflow, target size,
contrast, axe) then do not run, so prefer the producer plus `--auth-state` and keep Cypress for journeys.

Rules: the state file lives outside the repo or is ignored by git (the tool refuses it otherwise); values are never printed; the seed runs
only in the top frame of the named origin; a producer never takes a credential from the command line.
