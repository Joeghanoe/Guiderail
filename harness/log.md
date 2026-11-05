# Change log

## 2026-11-05

- Completed the public-tool CLI migration with 82 declared routes across 51 tool implementations; 23 libraries, provider adapters, hook handlers and fixtures remain explicitly internal. Added the [checked catalog](tools/cli/catalog.json) and [command reference](tools/cli/commands.md), native-argument forwarding, explicit stdin scope, raw output for pipelines, and guarded human-only operations. PR findings are validated before the existing pipeline writer runs. Updated public playbook and tool examples to use `tvh`. The process-step skills extension remains proposed.

## 2026-11-04

- Extended `tvh` with frontend capture/comparison, bounded streaming pipeline watches, greenfield initialization, and recorded design verification. Added native initial-skill-selection probes with observed tool-call evidence; workflow outcomes remain separate. Pipeline diagnosis stays a playbook and CLI operation, and installation removes the retired harness-owned skill adapter. The verify template now fails when its design gate is unavailable instead of silently passing design-only verification.
- Approved the [process-skills and unified-CLI proposal](../docs/adr/0009-process-skills-and-unified-cli.md), allowing breaking changes during development. Added the `tvh` pilot for guidance selection, project verification, independent change review, Azure DevOps diagnosis and restricted cloud/Sonar reads. Installation publishes the review skill for Claude Code and Copilot. At the owner's direction, pipeline diagnosis remains a playbook and CLI operation rather than a skill. Playbooks remain canonical; native findings and verification receipts retain their contracts.
- Captured [feedback on editor-dependent Sonar diagnostics](../feedback/headless-sonar-analysis-without-open-editor-files.md) and a [proposed local analysis tool](../docs/proposals/headless-sonar-analysis.md). The design uses Sonar Roslyn analyzers and ESLint with explicit scope and evidence. It preserves the server reader and records the proposed departure from E-016's IDE-first workflow. No runner, rule change or consumer adoption is active.

## 2026-11-03

- Moved audit documents, model comparisons, validation findings and raw execution evidence into the owner's local `$GOLDEN_PATH_HOME/testing/` storage. Preserved reusable checks, regression fixtures and benchmark definitions in Git. Installation creates the persistent testing directory; ignore rules keep run records out of the checkout.

## 2026-11-02

- Added checksum-pinned Gitleaks and a PSRule for Azure Key Vault pilot with real-engine calibration. Gitleaks scans current source in harness CI and PR commit ranges in adopting repositories. PSRule uses explicit deployment inputs; successful unchanged entry-template evidence suppresses only overlapping legacy IAC.4 literals. Usage lives in the [verification tools](tools/verification/index.md); calibration reports are local testing records.
- Made executable C# structural mechanics authoritative in the checker and removed the parallel detailed list from guidance. Kept semantic expectations and all existing examples. Recorded three exact historical fingerprints for synthetic redaction fixtures; current fixtures construct equivalent test output at runtime.

- Added a distributed, validated requirement registry and evidence receipts. Kept existing OKF types, rule IDs, example verdicts, reviewer thresholds and all examples. See [verification contracts](tools/verification/index.md).
- Integrated the existing CODE.5 Roslyn checker with baseline discovery, explicit conditional configurations, retained JSON and separate failure/error handling. The reusable PR template runs the check independently of guidance selection and publishes verification evidence.
- Replaced attempted-command and extension markers with successful, content-deduplicated edit-time retrieval for Claude and agy. Fixed the reviewer-eval trigger's stale selector path and covered supported adapters.
- Added regression fixtures and an owner-authorized synthetic agy smoke test. Preserved permission failures and timeout evidence alongside the successful verification-only follow-up. Implementation run evidence is stored locally under `$GOLDEN_PATH_HOME/testing/`. Copied bundles report unknown source revision instead of inheriting the consumer commit.

## 2026-11-01

- Added loop- and graph-based orchestration guidance: bounded work packages, named responsibilities, tiered models, explicit retry limits and reviewer checks for generated-code failures (`83be9a0`).
- Added formatting/linting configuration and tightened example prose while preserving the evaluation structure (`cd69482`, PR #17).
- Added a configurable Codex sandbox mode for benchmark adapters and published the greenfield-002 model comparison with its isolation and evidence limits (PR #18; `8d807b7`).
- Added the development-process coverage discussion proposal for colleague interviews. Its merge records publication of the proposal, not acceptance of its proposed capabilities (PR #19).
- Adopted one central YAML configuration location for deployment settings and resource names, with run choices exposed as clearly labelled parameters. Added and approved E-044, E-045 and E-049. The owner-run Azure pipeline confirmed the runtime-variable composition after the original nested compile-time assertion failed. The predecessor checkout contains the 75ffc94 experiment, runtime-check fix 6c3c4a7 and display-name correction 485da4b.
- Aligned the GitHub Actions example E-047 with the shared/environment YAML convention. Adapted the inspected reference repository's reusable loader and environment workflow; kept source refs consistent and used JSON outputs for workflow consumers.
- Added and approved E-037, E-038, E-041 and E-048 for APIM product access, authorized cloud reads, guard clauses and simple conditional expressions, including a switch alternative. Eight new examples produced 15 passing scenarios with AGY `gemini-3.8-flash-high` through eval-queue on bundle `c3bf11769e`.
- Promoted E-021, E-023, E-024, E-025, E-027, E-028, E-029, E-030, E-031, E-032, E-033, E-035 and E-036 using the owner's acceptance and complete historical passing scenario sets. Preserved model-specific failures and the original advisory/gating classifications in the recorded results.
- Kept BannedSymbols/analyzer files and scenario-mapping machinery opt-in for consumer repositories. Corrected setup guidance and added scaffold regression coverage. The owner declined the narrower E-039, E-040, E-042, E-043 and E-046 reviewer cases.
- Recorded prior owner adoption of CODE.8, CODE.10, DEL.4, DEL.5, OBS.3, T.6 and start-greenfield from targeted merged PRs, with approval commits on those documents. Marked the tested design-check and OpenAPI-drift gate descriptions stable.
- Recorded the owner's explicit approval of CODE.7, CODE.9, CODE.11, OBS.2, UI.1, UI.2 and the remaining operational playbooks. The owner confirmed write-business-test-plan had supported acceptance testing. All active rules, gates and playbooks are stable.
- Removed E-034 and its dedicated fixture at the owner's request. Historical eval evidence, including its failed bad case, remains in the result records; its identifier is not reused.
- Recorded the owner's approval of [ADRs 0001–0007](../docs/adr/). Kept ADR 0008, the development-process proposal and the knowledge-base incident-triage automation idea open for separate review.
- Moved processed feedback to [docs/feedback/processed](../docs/feedback/processed/), retained the [current conventions](../docs/decisions/feedback-conventions.md) as an editable record, and documented [example verdicts, lifecycle and evaluation results](../docs/example-verdicts.md). Removed the temporary draft-approval audit after preserving useful provenance.
- Adopted this OKF [log.md](log.md) summary format from Vegviser. Entries describe material changes and rationale, newest date first; Git retains the authoritative diff and history. Current conventions and ADRs retain their own authority and lifecycle.

## 2026-10-31

- Merged the design-first greenfield workflow, including DEL.4, CODE.8, OBS.3, the design gate, scaffold command and before-code verification steps (PR #5, `fa181d8`). The feature's preparation and benchmark work began on 30 October.
- Added per-run token, cache, duration and cost reporting, preserving unknown metrics as unknown. Extended AGY usage capture and made eval-queue run scenarios concurrently with a sliding window (`a945be9`, `0465946`, `d7709e1`).
- Recorded a full reviewer-evaluation result for `d7709e1`: all 44 gating scenarios passed; 32 of 33 advisory scenarios passed. The failed E-034 bad case remained visible in the evidence (`a0bd751`; `tools/review/history.jsonl`).
- Added ADR 0007's owner decisions on evaluation evidence, harness ownership, working modes and measurement (`3c51aeb`). Added ADR 0008 as a proposal for automatic feedback classification; it did not implement or approve that capability (`1d0bed0`).
- Made Directory.Build.props and BannedSymbols.txt optional for consumer repositories instead of scaffolded requirements (PR #6). Added authentication-state support to screenshot capture for locally reachable pages behind login (PR #7).
- Corrected command guards to judge command behavior rather than reject harmless occurrences of words in quoted data (PR #8). This retained the read-only and secret-protection boundaries.
- Added T.6 real-dependency evidence for adapters (PR #9), a web-app design profile based on ports and health rather than service-specific roles (PR #10), and polyglot verification plus first-commit handling (PR #11).
- Added CODE.9 to address input-size bounds, algorithm shape and honest reporting of truncated searches (`1a15578`). Added CODE.10 for derived-value ownership and consistency (PR #14) and DEL.5 for generated API contracts and drift checks (PR #13).
- Added a decomposition trigger for work spanning multiple layers (PR #15) and a style-guide contrast checker before frontend construction (PR #16).

## 2026-10-30

- Renamed cases to examples and evaluations to benchmarks, retaining the source material in the new locations (`49166ef`).
- Prepared the design-first workflow, solution-design template, scaffold and design checker on the feature branch. Added the design-only gate before source creation, design-before-code trace measurements, and the event-sink role (`bec27e8`, `f4fe08b`, `62424c6`, `bef1c6c`). This work was merged on 31 October.
- Added neutral examples and brownfield evaluation cases distilled from source projects, with training, validation and holdout separation. Consolidated example identifiers instead of preserving source-project numbering (`b521187`, `3e2c03f`).
- Extended example-driven evaluations with context fixtures and recorded greenfield improvement-loop evidence (`0ce547c`). Added Codex evaluation support and the brownfield candidate runner with separate adapters and graders (`6d980df`, `263e9a6`).
- Added evidence-based diagnosis of benchmark runs so evaluator/setup problems can be distinguished from candidate failures (`b810a9b`).

## 2026-10-29

- Added supporting tools and playbooks for dependency lookup, local diagnostics, build timing, UI comparison, specification notes, repository-convention discovery, coverage impact and prose-density checks (`ce3d4e8`).
- Made orchestration model-agnostic through configured model tiers and provider-neutral work packages (PR #1). Added resumable eval-queue checklists so completed scenarios survive interrupted runs (`6c13241`).
- Added and corrected Windows Git Bash/macOS portability for installation and tool execution (PR #2). Clarified principle references and dependency-health guidance while developing the agentic-SDLC harness (PR #3).
- Added and hardened the deterministic CODE.5 structural checker, with fixtures in CI and documented enforcement limits (PR #4).
- Added frozen evaluation inputs, backup grading, provider adapters for Claude and Codex, and isolated container candidate execution. Corrected the container image/profile and portable path handling (`11d81ff`, `88ff417`, `cfc2473`, `686e1a8`, `47267ba`).
- Added ADRs 0001–0006 and refined the proposed responsibility and evaluation boundaries. These were proposals at this date; their later approval is recorded under 1 November (`5b70e2c`, `193a44d`).
- Consolidated installation and runtime state under GOLDEN_PATH_HOME, retired the older harness aliases, and separated evaluation material and infrastructure scripts from the knowledge bundle (`aaa1629`, `fb451fd`).

## 2026-10-28

- Created the CodingHarness repository and imported the existing shared harness: OKF knowledge, rules, examples, read-only wrappers, agent hooks/adapters, installation, review/evaluation tools and CI configuration (`ae84ee8`, `f5436a3`). Earlier entries below belong to the Azure DevOps predecessor, TeamValue.AiHub.GitHubCopilot, inspected through the TeamValue.AiHub.Harness checkout; their commit IDs belong to that repository rather than this one. Dates record source commits or merges, not inferred approval dates.

## 2026-10-27

- Added UI.2 for goal-focused screens and DEL.3 for focused, evidenced changes. Added workload orchestration, the always-loaded context budget, IaC settings checks and AGY reviewer support (7751988).
- Integrated review-evaluation execution and CI change detection in the predecessor harness, while documenting evidence limits and preserving the reviewer thresholds (7751988).

## 2026-10-26

- Improved the review-and-fix adapter, command guards and read-wrapper behavior (860fcf6). Added the one-type-per-file example for C# and TypeScript (576dc6d, 8a9d709).
- Added frontend verification: UI.1, the verify-frontend playbook, and responsive screenshot capture with automated UI checks (fb38635).

## 2026-10-25

- Added the local review-and-fix workflow and findings rendering, with findings tracked as fixed, skipped or unchanged. Added CODE.7 for linked changes across code, configuration, documentation and queries (eb4f94f).
- Allowed agents to push an explicitly named feature branch while retaining human control over default/release branches and irreversible actions (331b9a9).
- Published proposals for Vegviser as the knowledge layer and the harness as router/enforcer. These records were proposals, not approval of a new cross-repository authority model (47f8a43, 0d4bb8f).

## 2026-10-23

- Added formatted Azure DevOps PR-thread reads and allowed read-only REST/invoke forms through the cloud wrapper using the authorized current login. Refined environment-promotion boundaries and the read-only operational playbooks (8d68fb0).

## 2026-10-22

- Added the read-only incident-triage and deployment-verification playbooks. Captured APIM access and Azure read-access feedback for later processing (c39f5d5).

## 2026-10-21

- Added evaluation context fixtures, concurrent execution and reviewer regression tests so snippets could be assessed with relevant surrounding files (143f15a).
- Added Azure DevOps helpers for failed-run diagnosis and live run monitoring, with a shared read-only access implementation and a diagnosis playbook (fa5c89d).

## 2026-10-20

- Added the broad read-verb boundary case, reorganized harness tools by domain and introduced the tools index (581518e, c34d31d).
- Added the business-test-plan playbook and JSON-to-workbook generator for acceptance testing (95b7f34). Added ServiceNow read tooling (1fee35b).
- Added data-driven draw.io generation from JSON specifications and improved missing-logo handling (d1d7928, c7ad6ef).
- Refactored AI review and its evaluation thresholds, then added Copilot as another evaluation engine (e575a09, 67da725, 7899039). The imported history retains the unsuccessful early evaluation result rather than treating the new tooling as proof of reviewer quality.

## 2026-10-19

- Added the Sonar read wrapper, token-safe access guidance and examples for static-analysis reads and use of the authorized current cloud login (95f151d).
- Added OBS.2 on alert causality and absence of expected signals (b3649ab).

## 2026-10-18

- Replaced the predecessor agent/skill-plugin structure with an OKF harness: shared base instructions, principles, rules, cases, review/feedback playbooks, command hooks, read wrappers, installation and CI (1aa13f7).
- Added worked cases and the feedback-to-example process, then expanded code-hygiene, IaC and health guidance. Human-verification metadata was added to accepted cases; the diagnostics case was explicitly returned to draft instead of retaining unsupported acceptance (60beff0, 51bf659, e8dfdf6, 8a663d6).
- Changed harness distribution from copying/synchronizing runtime instructions into consumer repositories to a pinned shared harness, with thin agent adapters and updated guards (51bf659).
