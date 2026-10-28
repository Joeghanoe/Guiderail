# Tools

Scripts grouped by the system or concern they serve. Open the folder your task touches. Agents reach cloud and
Sonar only through the read wrappers (CLD.1, SEC.2); the guard hook and the install allow rules name those paths.

* [harness/](harness/) - `bundle.py` selects rules, checks the bundle and private-artifact boundary, validates findings, builds indexes, and prepares feedback worktrees; `check-adapter.sh` verifies the rules reached an agent's context
* [review/](review/) - `review.sh` runs the AI review for one change; `render.py` shows its findings as a readable summary (playbook: review-and-fix); `eval.py` evaluates the same review flow against cases, with `thresholds.json` as its gate
* [testing/](testing/) - `check-scenarios.py` is the T.5 gate: a change that reaches the integration suite needs a scenario or a waiver; `business-testplan.py` builds the business end-to-end test plan workbook from a spec (playbook: write-business-test-plan)
* [iac/](iac/) - `check-iac.py` is the gate for IAC.2, IAC.3 and IAC.4: a Bicep or HCL file that explicitly sets a network default action to Allow, a TLS minimum below 1.2, or Key Vault protections to false fails the PR
* [cloud/](cloud/) - `cloud-read.sh` is the read-only wrapper for `az`, `terraform`, `kubectl` and `hcloud` (CLD.1)
* [azure-devops/](azure-devops/) - `ado-post-findings.sh` posts review findings to a pull request; `ado-mine-review-comments.py` mines review threads into an anonymised CSV; `ado-run-failure.sh` is the read-only view of a failed run (failed tasks, errors, log tails) and `ado-run-watch.sh` follows a running one until it ends, one line per change, for the Monitor tool; both share `ado-common.sh` (playbook: diagnose-pipeline-failure)
* [servicenow/](servicenow/index.md) - `sn-get.sh` is the read-only wrapper for the ServiceNow Table API (allowlisted configuration tables, credentials off the command line); `sn-access-check.sh` shows which tables the account can read; see its routing table in `servicenow/index.md` (playbook: analyse-servicenow)
* [frontend/](frontend/) - `screenshot.mjs` screenshots a running page at phone, tablet and desktop widths and runs the responsive and WCAG checks, for the AI to look at (rules UI.1, UI.2; playbook: verify-frontend)
* [diagrams/](diagrams/) - `dk` builds a one-page draw.io diagram (plus SVG and PNG preview) from a JSON spec, with logos, real draw.io icons, numbered legend and a name tile when a logo is missing; `dk logo` looks up and downloads a software logo, `dk icons` finds icon paths (playbook: draw-integration-diagram)
* [orchestration/](orchestration/) - `orchestrate.py` decomposes complex workloads into subagent work packages and classifies model tiers (`economy`, `builder`, `reasoner`) to optimize token spend (playbook: orchestrate-workload)
* [sonar/](sonar/) - `sonar-read.sh` is the read-only wrapper for the Sonar API, keeping the token off the command line (SEC.2)

New script: put it in the folder of the system it talks to; create a folder when a new system appears, and add a line here.
