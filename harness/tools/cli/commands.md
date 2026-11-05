# Public commands and internal implementations

This reference comes from [catalog.json](catalog.json). Use `tvh tools --check --json` to verify coverage.

For declared native routes, place CLI controls before `--` and native arguments after it. Use `--json` for the execution envelope or `--raw` for native stdout. Human-only commands require `--interactive` in a terminal and do not capture credentials.

| Command | Implementation | Effects |
| --- | --- | --- |
| `tvh ado pr mine-comments` | [azure-devops/ado-mine-review-comments.py](../azure-devops/ado-mine-review-comments.py) | network-read, credential-use, artifact-write; human terminal only |
| `tvh ado pr post-findings` | [azure-devops/ado-post-findings.sh](../azure-devops/ado-post-findings.sh) | external-write, pipeline-identity |
| `tvh ado pr threads` | [azure-devops/ado-pr-threads.sh](../azure-devops/ado-pr-threads.sh) | network-read, credential-use |
| `tvh ado run diagnose` | [azure-devops/ado-run-failure.sh](../azure-devops/ado-run-failure.sh) | see CLI contract |
| `tvh ado run timing` | [azure-devops/ado-run-timing.sh](../azure-devops/ado-run-timing.sh) | network-read, credential-use |
| `tvh ado run watch` | [azure-devops/ado-run-watch.sh](../azure-devops/ado-run-watch.sh) | see CLI contract |
| `tvh benchmark artifacts` | [testing/freeze_eval.py](../testing/freeze_eval.py) | artifact-write |
| `tvh benchmark brownfield grade` | [testing/run_brownfield.py](../testing/run_brownfield.py) | local-execution, artifact-write |
| `tvh benchmark brownfield run` | [testing/run_brownfield.py](../testing/run_brownfield.py) | local-execution, artifact-write |
| `tvh benchmark candidate freeze` | [testing/run_candidate.py](../testing/run_candidate.py) | artifact-write |
| `tvh benchmark candidate login` | [testing/run_candidate.py](../testing/run_candidate.py) | interactive-authentication; human terminal only |
| `tvh benchmark candidate rescore` | [testing/run_candidate.py](../testing/run_candidate.py) | local-execution, artifact-write |
| `tvh benchmark candidate run` | [testing/run_candidate.py](../testing/run_candidate.py) | local-execution, artifact-write |
| `tvh benchmark diagnose propose` | [testing/diagnose_run.py](../testing/diagnose_run.py) | runtime-state-write |
| `tvh benchmark diagnose record` | [testing/diagnose_run.py](../testing/diagnose_run.py) | runtime-state-write |
| `tvh benchmark grade-backup` | [testing/backup_eval.py](../testing/backup_eval.py) | local-execution, artifact-write |
| `tvh benchmark image-build` | [testing/container/build.sh](../testing/container/build.sh) | container-build, network-read |
| `tvh benchmark usage` | [testing/harness_usage.py](../testing/harness_usage.py) | local-read, optional-artifact-write |
| `tvh bundle budget` | [harness/bundle.py](../harness/bundle.py) | local-read |
| `tvh bundle check` | [harness/bundle.py](../harness/bundle.py) | local-read |
| `tvh bundle check-example` | [harness/bundle.py](../harness/bundle.py) | local-read |
| `tvh bundle index` | [harness/bundle.py](../harness/bundle.py) | harness-write |
| `tvh bundle privacy-check` | [harness/bundle.py](../harness/bundle.py) | local-read |
| `tvh bundle submit-feedback` | [harness/bundle.py](../harness/bundle.py) | harness-write |
| `tvh checks code-types` | [verification/verify.py](../verification/verify.py) | local-execution, artifact-write |
| `tvh checks iac` | [iac/check-iac.py](../iac/check-iac.py) | local-read |
| `tvh checks install-tools` | [verification/install-tools.py](../verification/install-tools.py) | network-read, executable-install |
| `tvh checks keyvault` | [verification/verify.py](../verification/verify.py) | local-execution, artifact-write |
| `tvh checks node` | [code/node-verify.sh](../code/node-verify.sh) | local-execution, dependency-install |
| `tvh checks openapi` | [code/openapi-drift.py](../code/openapi-drift.py) | local-read |
| `tvh checks registry` | [verification/verify.py](../verification/verify.py) | local-read |
| `tvh checks report` | [verification/verify.py](../verification/verify.py) | local-read, artifact-write |
| `tvh checks review-plan` | [verification/verify.py](../verification/verify.py) | local-read, artifact-write |
| `tvh checks run` | [verification/verify.py](../verification/verify.py) | local-execution, artifact-write |
| `tvh checks scenarios` | [testing/check-scenarios.py](../testing/check-scenarios.py) | local-read |
| `tvh checks secrets` | [verification/verify.py](../verification/verify.py) | local-execution, artifact-write |
| `tvh checks test-presence` | [code/test-presence.sh](../code/test-presence.sh) | local-read |
| `tvh cloud read` | [cloud/cloud-read.sh](../cloud/cloud-read.sh) | see CLI contract |
| `tvh code types` | [code/Program.cs](../code/Program.cs) | local-execution, artifact-write |
| `tvh context candidates` | [harness/density.py](../harness/density.py) | local-read |
| `tvh context check-adapter` | [harness/check-adapter.sh](../harness/check-adapter.sh) | model-call |
| `tvh context duplicates` | [harness/density.py](../harness/density.py) | local-read |
| `tvh context report` | [harness/density.py](../harness/density.py) | local-read |
| `tvh context select` | [harness/bundle.py](../harness/bundle.py) | see CLI contract |
| `tvh deps currency` | [deps/check-currency.py](../deps/check-currency.py) | local-read |
| `tvh deps read` | [deps/dep-read.sh](../deps/dep-read.sh) | local-read, optional-network-read |
| `tvh dev read` | [dev/dev-read.sh](../dev/dev-read.sh) | local-service-read, redacted-output |
| `tvh diagram build` | [diagrams/dk](../diagrams/dk) | artifact-write, optional-network-read |
| `tvh diagram icons` | [diagrams/dk](../diagrams/dk) | local-read |
| `tvh diagram logo` | [diagrams/dk](../diagrams/dk) | artifact-write, optional-network-read |
| `tvh doctor` | [cli/main.py](../cli/main.py) | see CLI contract |
| `tvh eval queue reset` | [review/eval-queue.py](../review/eval-queue.py) | runtime-state-write |
| `tvh eval queue run` | [review/eval-queue.py](../review/eval-queue.py) | model-call, runtime-state-write |
| `tvh eval queue status` | [review/eval-queue.py](../review/eval-queue.py) | local-read |
| `tvh eval reviewer` | [review/eval.py](../review/eval.py) | model-call, artifact-write |
| `tvh eval skills` | [testing/process_skills.py](../testing/process_skills.py) | see CLI contract |
| `tvh findings render` | [review/render.py](../review/render.py) | local-read |
| `tvh findings validate` | [harness/bundle.py](../harness/bundle.py) | local-read |
| `tvh frontend auth-msal` | [frontend/auth-examples/msal-client-credentials.mjs](../frontend/auth-examples/msal-client-credentials.mjs) | credential-use, token-file-write, network-read; human terminal only |
| `tvh frontend capture` | [frontend/screenshot.mjs](../frontend/screenshot.mjs) | see CLI contract |
| `tvh frontend compare` | [frontend/compare-ui.mjs](../frontend/compare-ui.mjs) | see CLI contract |
| `tvh frontend contrast` | [frontend/contrast.mjs](../frontend/contrast.mjs) | local-read |
| `tvh greenfield check` | [greenfield/design-check.py](../greenfield/design-check.py) | local-read |
| `tvh greenfield init` | [greenfield/greenfield-init.sh](../greenfield/greenfield-init.sh) | see CLI contract |
| `tvh orchestrate layers` | [orchestration/orchestrate.py](../orchestration/orchestrate.py) | local-read |
| `tvh orchestrate plan` | [orchestration/orchestrate.py](../orchestration/orchestrate.py) | local-read |
| `tvh orchestrate tier` | [orchestration/orchestrate.py](../orchestration/orchestrate.py) | local-read |
| `tvh project verify-config init` | [code/project-verify.sh](../code/project-verify.sh) | local-write |
| `tvh project verify-config path` | [code/project-verify.sh](../code/project-verify.sh) | local-read |
| `tvh review` | [review/review.sh](../review/review.sh) | see CLI contract |
| `tvh scaffold brief` | [scaffold/read-conventions.py](../scaffold/read-conventions.py) | local-read |
| `tvh scaffold kinds` | [scaffold/read-conventions.py](../scaffold/read-conventions.py) | local-read |
| `tvh servicenow access` | [servicenow/sn-access-check.sh](../servicenow/sn-access-check.sh) | network-read, credential-use |
| `tvh servicenow get` | [servicenow/sn-get.sh](../servicenow/sn-get.sh) | network-read, credential-use |
| `tvh sonar read` | [sonar/sonar-read.sh](../sonar/sonar-read.sh) | see CLI contract |
| `tvh spec list` | [spec/spec-note.py](../spec/spec-note.py) | local-read |
| `tvh spec new` | [spec/spec-note.py](../spec/spec-note.py) | vault-write |
| `tvh spec set` | [spec/spec-note.py](../spec/spec-note.py) | vault-write |
| `tvh testing business-plan` | [testing/business-testplan.py](../testing/business-testplan.py) | artifact-write |
| `tvh testing coverage` | [testing/coverage-impact.py](../testing/coverage-impact.py) | local-read |
| `tvh tools` | [cli/catalog.py](../cli/catalog.py) | see CLI contract |
| `tvh verify` | [code/project-verify.sh](../code/project-verify.sh) | see CLI contract |

## Internal implementations

These are reached through the public commands or hook/profile protocols. They are not separate agent-facing commands.

| File | Reason |
| --- | --- |
| [azure-devops/ado-common.sh](../azure-devops/ado-common.sh) | Sourced identity and HTTP helpers. |
| [cli/workflows.py](../cli/workflows.py) | Explicit CLI workflow argument and dispatch helpers. |
| [diagrams/drawio_kit/__init__.py](../diagrams/drawio_kit/__init__.py) | Diagram package implementation reached through diagram commands. |
| [diagrams/drawio_kit/__main__.py](../diagrams/drawio_kit/__main__.py) | Diagram package implementation reached through diagram commands. |
| [diagrams/drawio_kit/core.py](../diagrams/drawio_kit/core.py) | Diagram package implementation reached through diagram commands. |
| [diagrams/drawio_kit/layouts/__init__.py](../diagrams/drawio_kit/layouts/__init__.py) | Diagram package implementation reached through diagram commands. |
| [diagrams/drawio_kit/layouts/lane_matrix.py](../diagrams/drawio_kit/layouts/lane_matrix.py) | Diagram package implementation reached through diagram commands. |
| [diagrams/drawio_kit/logos.py](../diagrams/drawio_kit/logos.py) | Diagram package implementation reached through diagram commands. |
| [frontend/auth-state.mjs](../frontend/auth-state.mjs) | Browser authentication-state parsing and seeding library. |
| [harness/context.py](../harness/context.py) | Edit-hook protocol adapter. |
| [review/run-agy.py](../review/run-agy.py) | Provider implementation invoked by review and evaluation commands. |
| [review/run-claude.py](../review/run-claude.py) | Provider implementation invoked by review and evaluation commands. |
| [review/run-codex.py](../review/run-codex.py) | Provider implementation invoked by review and evaluation commands. |
| [review/run-copilot.py](../review/run-copilot.py) | Provider implementation invoked by review and evaluation commands. |
| [review/usage.py](../review/usage.py) | Usage normalization library. |
| [testing/adapters/agy.py](../testing/adapters/agy.py) | Provider or grader adapter invoked through benchmark profiles. |
| [testing/adapters/claude_code.py](../testing/adapters/claude_code.py) | Provider or grader adapter invoked through benchmark profiles. |
| [testing/adapters/codex.py](../testing/adapters/codex.py) | Provider or grader adapter invoked through benchmark profiles. |
| [testing/adapters/common.py](../testing/adapters/common.py) | Provider or grader adapter invoked through benchmark profiles. |
| [testing/adapters/grader_agy.py](../testing/adapters/grader_agy.py) | Provider or grader adapter invoked through benchmark profiles. |
| [testing/brownfield-verify.sh](../testing/brownfield-verify.sh) | Snapshot verification fixture installed by the brownfield runner. |
| [verification/keyvault.ps1](../verification/keyvault.ps1) | PowerShell scanner implementation used by checks keyvault. |
| [verification/standard_checks.py](../verification/standard_checks.py) | Scanner adapters used by checks commands. |
