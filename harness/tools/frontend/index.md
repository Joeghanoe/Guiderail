# Frontend Tools

Agent-facing capture and comparison use `tvh frontend capture` and `tvh frontend compare`; see the [CLI contract](../cli/index.md). These retain the native reports below. CLI comparison maps a regression to exit 1 and incomplete execution to exit 2; the native script's exits differ.

* [screenshot.mjs](screenshot.mjs) - screenshots a running page at phone, tablet and desktop widths and runs the responsive and WCAG checks, writing `report.json` (rules UI.1, UI.2; playbook: verify-frontend); `--auth-state` captures pages behind a login by seeding storage and cookies before the app boots
* [auth-state.mjs](auth-state.mjs) - the format, validation and seed script of an auth state file (values are never printed; the seed runs only in the top frame of one origin)
* [auth-examples/](auth-examples/index.md) - producers of a state file, for example MSAL with client credentials
* [compare-ui.mjs](compare-ui.mjs) - compares two [screenshot.mjs](screenshot.mjs) runs and reports fixed, new, reduced and unchanged findings per viewport; exit 2 when a fix introduced a new finding; it bounds regression risk and does not score the design (playbook: verify-frontend)
* [contrast.mjs](contrast.mjs) - checks the colour tokens of a style guide against WCAG 2.2 contrast (4.5:1 small text, 3:1 large text) before screens are built from them; exit 1 on a failing pair (rule UI.1; playbook: verify-frontend)
