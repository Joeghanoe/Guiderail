# Engineering standards and accepted decisions

This records the classification of six Loop pages supplied as exports and the user-approved harness decisions below. Source classification remains preliminary; the decisions have been applied to the relevant harness guidance. References identify Loop page titles and section IDs. The exports contain only truncated Loop print URLs, so full source links remain to be supplied. A principle expresses a durable intent or trade-off; a work instruction specifies a process, product, configuration or implementation. A mandatory instruction can still be binding within its stated scope without being a principle. Labels in the source do not settle the classification.

| Source | Principle-level intent | Instructions or standards embedded in the source | Scope and uncertainty |
|---|---|---|---|
| Loop page "Architectural Principles" | A.1 preference for SaaS; A.8 independent services; A.9 stable interfaces; A.12 single responsibility; A.20 cost trade-offs; controlled autonomy and bounded impact | A.3 one language/framework per domain; A.10 one identity system; controlled-autonomy implementation layers, approval gates and specific controls | Golden Path is the stated scope; do not assume every example or implementation applies everywhere. The document also labels very specific mandates as principles. |
| Loop page "Business Analytics principles" | Customer value (BT8), evidence and perspective (BT9), long-term value (BT10), simplify (BT11), action (BT12), shared vision (BT14) | Regular customer interaction and rigorous validation are practices implementing those intents | BT13 explicitly says it is to be merged with BT11; its status needs confirmation. |
| Loop page "Cloud Principles" | Privacy, least privilege, observability, auditability, testability and minimizing surprise are durable intents | Four-eyes approval, automated key rollover, roll-forward, Git and n-1 framework currency are concrete policies or practices | Verify scope and approval separately. The source says current version *and* immediate predecessor are supported (section "Supported frameworks are always n-1"); the approved shorthand is n-1, as defined by DEL.2. |
| Loop page "Data Minimization Principles" | Collect, retain, access and share only what is needed; maintain quality and security | Retention/deletion, processing restrictions, anonymisation and compliance documentation are operational obligations requiring context and approved retention rules | Do not infer a universal retention period or treat anonymisation as always applicable. |
| Loop page "Data Principles" | Data ownership, governed sharing, fit-for-purpose storage, resilience, integrity, interoperability | D.2 W3C tracing, D.3 named approval, D.11 UTC/SI/UTF-8, D.12 Purview and ABAC are concrete standards or vendor-specific controls | D.12's named product is part of the source's stated mandate but is not itself the underlying principle; applicability and exceptions need review. |
| Loop page "IntegrationHub Principles" | Shared domain language, decoupling, minimum event data, least privilege and end-to-end observability | IH3 Service Bus queues, IH5 Event Grid, IH6 API Management, IH9 CorrelationId, IH10 `/health` and two availability-test locations are solution-specific implementation instructions | The Loop page explicitly limits these to IntegrationHub; IH11 is listed as future. Do not turn them into general company-wide rules. |

## Sign-off

The user signed off on every decision in this document on 2026-10-29 and stated that all open decisions were
tackled. Preliminary source classification and the later validation phases keep their own review points.
Project roles supplied the same day: `D:/Prototypes/TV/Bizure.Backups` is the Phase 3 example (calibration
reference, never a holdout); `D:/Prototypes/TV/TeamValue.IntegrationHub.Connectors` and
`D:/Prototypes/TV/TeamValue.IntegrationHub.Platform` are validation/reference projects for now, with
calibration or holdout assignment still to be made when further projects arrive.

## Decisions accepted on 2026-10-29

- External dependencies remain observable; OBS.1 distinguishes unusable services, partially available capabilities and tenant-specific outages.
- P2 prefers asynchronous events for business state changes and governed synchronous paths for reads and immediate responses. The harness does not require a specific gateway or broker.
- P8 uses W3C execution trace context alongside a stable business/event correlation identifier where workflows span retries or multiple traces.
- P9 prohibits shared mutable operational stores across service ownership boundaries and permits governed reporting and analytical read models.
- Use **n-1** wording. DEL.2 continues to define the current-or-previous stable window.
- The harness is product-agnostic. Project-specific instructions stay in their projects; underlying principles and generalized cases may inform the harness. Named products in the source table are evidence about the sources, not requirements imported into this harness.
- CODE.5 remains an approved convention. Single service responsibility does not itself imply one type per file. The generated-file, partial-declaration, private nested-helper and changed-declaration scope was approved and implemented in the C# structural check.

## Initial project evidence (not an audit)

- `D:/Prototypes/TV/Bizure.Backups/src/Bizure.Backup/Bizure.Backup.csproj` targets `net10.0`; the project's `AGENTS.md` describes cross-cloud backup and a federated credential. Neither observation establishes compliance with framework policy or all identity requirements.
- `D:/Prototypes/TV/TeamValue.IntegrationHub.Connectors/src/` contains connector-specific health registrations and an AzureActiveDirectory function using a `CorrelationId`. These are examples to investigate, not evidence that all connectors meet IH9 or IH10.
- Both supplied top-level directories lack Git metadata; establish immutable source snapshots or commits before evaluation. Integration contains separate Platform and Connectors directories, whose origin and revisions need confirmation.

## Remaining implementation work

No further policy decision is required for the agreed CODE.5 scope and evaluation criteria.

- CODE.5 fixtures now run through tests/run.sh and CI; this gates checker regressions, not consumer-project compliance.
- Complete the standards catalog with explicit rule versions, enforcement, exceptions and evidence references.
- Add neutral fixtures for communication boundaries, trace propagation, store ownership and dependency health.
- Complete the command-policy regression and bypass test run, and address any failures.
- Produce a reproducible evidence report with separate deterministic, policy, behavioral and outcome dimensions, representing unsupported checks as inconclusive or not applicable.
- Obtain full Loop URLs and immutable revisions or snapshot identifiers for the supplied project evidence.

BT13's merge note is a source-maintenance question; it does not block these changes. Greenfield business
acceptance and calibration/holdout assignments belong to later validation phases.

## CODE.5 structural scope approved

On 2026-10-29 the user approved generated-file exclusion, separate partial declarations, private nested
helpers, and checking added or changed declarations without unrelated cleanup. The implementation is in
`harness/tools/code/`; `tests/test_code_types.py` runs fixed pass/fail/error fixtures in disposable trees.
JSON output records findings, applicability and errors. No model self-report contributes to this score.
The tool is explicitly invoked; it is not yet wired as an automatic pipeline gate. Other design concerns
remain review responsibilities. The fixture criteria are approved; reviewer thresholds are unchanged.
