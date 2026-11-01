# Feedback conventions

Last reviewed: 2026-11-01. The owner approved the retained examples in this session.

This is an editable record of current decisions, not an ADR. Revise a decision when experience changes it, record the reason in the history, and update its examples and checks. Git preserves earlier wording. Processed feedback lives in [the source records](../feedback/processed/); the active queue contains undecided feedback only.

## Current disposition

All active harness examples, rules, gates and playbooks are stable. The owner removed E-034 and its dedicated fixture on 2026-11-01; historical eval results remain intact. ADRs 0001–0007 are approved by the owner. Decision approval does not assert that every implementation/verification criterion has been completed.

Still open: ADR 0008, the development-process proposal and the knowledge-base incident-triage automation idea. The owner plans to review these later this week. The dated sections below preserve the earlier audit history and are superseded by this current disposition where statuses differ.

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
| Existing automation | E-016's Sonar read wrapper is implemented and has deterministic tests. Its historical automation-candidate verdict is not an unfinished reviewer eval. | `harness/tools/sonar/sonar-read.sh`; wrapper and guard checks in `tests/run.sh` |
| Specific incident regressions | Do not promote the error-code/runbook, telemetry-query, optional-gate or symlink cases into reviewer examples just to preserve a past incident. The owner declined E-039, E-040, E-042, E-043 and E-046. | Source feedback preserved as processed records where available |

The broader incident-triage automation idea remains undecided and stays in the feedback queue. This processing session does not approve that product work.

## History

| Date | Change | Reason |
| --- | --- | --- |
| 2026-11-01 | Accepted E-037, E-038, E-041, E-044, E-045, E-047, E-048 and E-049. | Owner reviewed and approved the retained cases. |
| 2026-11-01 | Used runtime macros in the nested Azure job check. | The initial pipeline compiled but a compile-time stage variable was empty; the corrected runtime check worked. |
| 2026-11-01 | Aligned GitHub's configuration layout with Azure's convention. | Preserve shared ownership across platforms while using a GitHub-native loader/output mechanism. |
| 2026-11-01 | Kept BannedSymbols and scenario-mapping machinery opt-in; declined five narrow reviewer cases. | Fix the setup rather than adding a reviewer expectation for every local incident. |

E-006 remains historical precedent for the earlier pipeline-owned naming convention. E-044 records the newly adopted central-directory convention; this session does not rewrite the older verified example.

## Historical evidence and example promotion

On 2026-11-01 the owner accepted promotion of examples that already had passing evaluation evidence. Promoted E-021, E-023, E-024, E-025, E-027, E-028, E-029, E-030, E-031, E-032, E-033, E-035 and E-036. Each has a complete passing scenario set in `harness/tools/review/eval-results.jsonl` under one recorded engine/model/bundle combination. The October 31 history summary also records a passing gating suite and 32 of 33 advisory scenarios passing.

Most snippets are unchanged since history commit `d7709e1`. E-032 and E-036 match the later committed snippets preceding their recorded passing Gemini Medium scenarios. This is historical evidence, not a fresh evaluation of the current full bundle. Promotion does not change the historical advisory/gating split or manufacture a current-bundle result.

E-034 remains draft because its bad scenario has a recorded failure and no complete passing set was found. E-021 is accepted with mixed model evidence: Gemini Low passed both scenarios, while Gemini Medium missed the bad case. Both results stay recorded. Stable examples define accepted expectations; a model-specific failure remains a reviewer regression, not a reason to change the expectation to make the gate pass.

## Rule, gate and playbook readiness

On 2026-11-01, corrected the stale draft labels on CODE.11 and the design-check and OpenAPI-drift gates. CODE.11 is the convention the owner explicitly approved through E-041/E-048; both gates are implemented and covered by deterministic tests. Gate stability records an implemented tool contract with documented limits, not proof of every consuming service.

The remaining 11 rule drafts and nine playbook drafts are not automatically promoted by example pass rates. They require review of the policy or workflow and evidence appropriate to their scope. Rules such as CODE.8 and DEL.5 have accepted examples supporting part of their scope, but those examples do not establish every clause. Tool tests for a helper do not by themselves demonstrate a whole operational playbook. ADRs retain their separately recorded approval status.

## Prior approvals recovered

On 2026-11-01, recovered prior owner adoption from merged PRs: #5 for CODE.8, DEL.4, OBS.3 and start-greenfield; #9 for T.6; #13 for DEL.5; #14 for CODE.10. Recorded the approval commits on those documents and corrected their stale draft labels. Subsequent explicit approvals resolved the other gaps, as recorded below. The temporary approval audit was removed after its outcome was captured here.

## Explicit approval of the remaining conventions

On 2026-11-01 the owner explicitly approved CODE.7, CODE.9, OBS.2, UI.1 and UI.2 and the diagnose-pipeline-failure, draw-integration-diagram, optimize-build-duration, review-and-fix, triage-incident, verify-deployment and verify-frontend playbooks. These twelve documents are stable, with the actual approval recorded in their metadata. This supersedes the earlier five-rule/eight-playbook pending count.

E-034 and write-business-test-plan remain draft. The separate incident-triage automation idea and ADR ratification remain undecided; approval of the triage playbook does not expand authorization to automate ticket intake, messages or cloud changes.

## Business test plan approval

On 2026-11-01 the owner explicitly approved write-business-test-plan and reported that it helped substantially with acceptance testing. Marked the playbook stable and recorded the approval. This supplies both acceptance and reported operational use; it does not imply every generated plan has been executed. E-034 is now the only remaining draft concept in the harness. Separate proposals and ADR ratification retain their existing status.

## E-034 removal and ADR approval

On 2026-11-01 the owner requested removal of E-034 and approved ADRs 0001–0007. Removed the example and its otherwise unused fixture, kept the historical pass/fail evidence, and recorded the actual ADR approval. ADR 0008 remains a proposal, as do the development-process proposal and incident-triage automation idea. No cloud permissions or runtime policy changes are made by these documentation updates.
