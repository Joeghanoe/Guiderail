# Frontend Tools

* `screenshot.mjs` - screenshots a running page at phone, tablet and desktop widths and runs the responsive and WCAG checks, writing `report.json` (rules UI.1, UI.2; playbook: verify-frontend)
* `compare-ui.mjs` - compares two `screenshot.mjs` runs and reports fixed, new, reduced and unchanged findings per viewport; exit 2 when a fix introduced a new finding; it bounds regression risk and does not score the design (playbook: verify-frontend)
