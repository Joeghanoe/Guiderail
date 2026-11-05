# Feedback conventions

Last reviewed: 2026-11-01. Owner: joeghanoe.

This is the editable record of current conventions. Change it when experience changes the decision, and update the affected rules, examples and checks. Summaries of what changed and why belong in [the change log](../../harness/log.md). Git remains the authoritative history; [processed source feedback](../feedback/processed/) preserves the original context.

## Current status

All active harness examples, rules, gates and playbooks are stable. E-034 and its dedicated fixture have been removed; historical eval results remain intact. ADRs 0001–0007 are approved. Decision approval does not assert that every implementation and verification criterion has been completed.

## Current decisions

| Topic | Decision | Examples or checks |
| --- | --- | --- |
| Pipeline configuration | Inputs represent run choices. One central configuration directory owns shared settings, environment settings and resource names. Deployment logic is reusable. | E-044 |
| Azure Pipelines | A shared `environments` variable drives `split`/`each`. Load environment and naming variable files at stage/job scope. Nested job templates consume runtime macros; do not assume they see stage variables during template expansion. | E-044, E-049; owner-run temporary pipeline |
| Run form labels | At least top-level parameters have concise display names that describe their purpose and follow existing vocabulary and capitalization. | E-045 |
| GitHub Actions | Align configuration ownership and YAML `name`/`value` files with Azure Pipelines. A reusable loader emits merged JSON for `fromJSON`; CI and release reuse an environment workflow. Keep refs consistent. Do not emulate Azure's template engine or force a matrix over promotion dependencies. | E-047, adapted from the inspected reference checkout |
| Control flow | Prefer guard clauses; omit else after a terminating branch. Simple value ternaries and clear switches are valid; nested ternaries choosing operations are not. | E-041, E-048; CODE.11 |
| API gateway access | Use API products and product-scoped subscriptions for subscription admission. Keep policy logic for controls the product boundary does not provide. | E-037 |
| Cloud reads | Authorized read-only wrapper requests can use the user's existing login. Do not require a second CLI configuration directory or allow writes, identity switching or credential reads. | E-038 and existing E-015 |
| Consumer-repo tooling | BannedSymbols/analyzer files and harness scenario mapping are opt-in. Do not scaffold or require them in other projects. Their use inside this harness can remain. | Scaffold regression test; existing optional gate guidance |
| Existing automation | E-016's Sonar read wrapper is implemented and has deterministic tests. Its historical automation-candidate verdict is not an unfinished reviewer eval. | [sonar-read.sh](../../harness/tools/sonar/sonar-read.sh); wrapper and guard checks in [run.sh](../../tests/run.sh) |
| Specific incident regressions | Do not promote the error-code/runbook, telemetry-query, optional-gate or symlink cases into reviewer examples just to preserve a past incident. The owner declined E-039, E-040, E-042, E-043 and E-046. | Source feedback preserved as processed records where available |

E-006 preserves precedent for the earlier pipeline-owned naming layout. E-044 records the newly adopted central configuration convention. Do not silently migrate an established repository while fixing an unrelated issue.

## Open work

- [Headless local Sonar analysis](../proposals/headless-sonar-analysis.md) is proposed through [draft feedback](../../feedback/headless-sonar-analysis-without-open-editor-files.md). It would analyze disk contents through C# analyzers and ESLint without opening editor files. E-016 and T.1 remain unchanged pending review; no local runner or consumer dependency has been added.
- [ADR 0008](../adr/0008-automatic-feedback-classification-and-drafts.md) remains a proposal; implementation is not approved by this record.
- [Development-process coverage](../proposals/development-process-coverage.md) remains a discussion proposal.
- [Knowledge-base incident triage](../../feedback/grounded-incident-triage-from-knowledge-base.md) remains an automation idea. Approval of the existing triage playbook does not approve automated ticket intake or external writes.

## Maintaining the record

After processing feedback, keep the current outcome here, move the source record out of the inbox, and add a short dated entry to [log.md](../../harness/log.md) linking the affected documents. Record the decision owner and the reason where they matter. Preserve contradictory or failed evidence; do not rewrite old eval results to match a new status.

This log convention follows TeamValue.Vegviser at `b7215fc`: the Documentation Standard keeps Git authoritative, and the Open Knowledge Format Interoperability Profile defines reserved [log.md](../../harness/log.md) files as newest-first dated change summaries. Material architectural choices remain in the ADRs.
