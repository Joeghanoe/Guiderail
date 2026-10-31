# Frontend Tools

* `screenshot.mjs` - screenshots a running page at phone, tablet and desktop widths and runs the responsive and WCAG checks, writing `report.json` (rules UI.1, UI.2; playbook: verify-frontend); `--auth-state` captures pages behind a login by seeding storage and cookies before the app boots
* `auth-state.mjs` - the format, validation and seed script of an auth state file (values are never printed; the seed runs only in the top frame of one origin)
* [auth-examples/](auth-examples/) - producers of a state file, for example MSAL with client credentials
* `compare-ui.mjs` - compares two `screenshot.mjs` runs and reports fixed, new, reduced and unchanged findings per viewport; exit 2 when a fix introduced a new finding; it bounds regression risk and does not score the design (playbook: verify-frontend)
