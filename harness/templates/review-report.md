# <Repository or change>: review findings

<Review date and reviewer. State the main conclusion and what must happen next. A release recommendation is advice, not approval.>

## Scope

<Repository, branch, full commit, diff base or repository-wide scope, included uncommitted changes, requested topics, exclusions and areas not inspected. State whether anything was fixed. Distinguish repository evidence from external state actually checked.>

| Check | Result |
| --- | --- |
| <Exact command and environment> | <Passed, failed, skipped or not run; counts and reason> |

<Explain failures and skipped coverage that limit the conclusion.>

## Decisions already taken

| Topic | Decision | Human decision reference |
| --- | --- | --- |
| <Trade-off> | <Accepted behavior and required mitigation> | <ADR, user instruction or other recorded decision> |

## Coverage against the spec

| Requirement and source | Implemented behavior and evidence | Missing, at risk or unverified |
| --- | --- | --- |
| <Requirement or acceptance criterion> | <Code path and test evidence> | <Gap and finding ID, or verification needed> |

<If no authoritative spec is available, say so and name the assumptions used.>

## Findings register

<Counts by severity and status, consistent with the rows. Use the harness severities: blocker, major, minor, nit. A blocker prevents the stated release or acceptance criterion; major means substantial security, correctness or reliability impact; minor means bounded impact; nit means low-impact cleanup. Explain scope-specific impact rather than copying severity from another project.>

| ID | Severity | Area | Finding | Evidence | Direction | Status |
| --- | --- | --- | --- | --- | --- | --- |
| F01 | <Severity> | <Area> | <Trigger and consequence> | <Full repo-relative path:line at reviewed commit; rule ID or quality note; confidence> | <Fix direction and verification> | <Open, fixed, accepted or no change needed> |

<Add detail under a finding ID when a row cannot hold the evidence. For fixes, give the change and verification result. For accepted findings, cite the human decision and remaining risk. An unverified risk must say which premise needs confirmation. Do not treat a proposed fix as completed work.>

## Dashboard and alerting

<Can operators verify the product's promised outcome? Trace actual telemetry fields, queries, thresholds, enabled rules and notification routes. Separate working behavior from gaps and reference finding IDs.>

## Operational readiness

<Relevant restore/recovery evidence, capacity, tenant isolation, onboarding and deployment risks. State the next release or customer milestone and which findings must close first. Omit this and other inapplicable sections for small changes.>

## Open verifications

| Finding or requirement | Unverified fact | Safe check and expected result |
| --- | --- | --- |
| <F01 or requirement> | <Precise uncertainty> | <Command or procedure, environment, expected evidence; who must run it if unavailable here> |

<Separate external state checks from local checks that did not run. An unanswered verification stays unverified.>
