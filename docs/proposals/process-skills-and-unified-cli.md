# Process skills backed by a unified harness CLI

Status: approved by joeghanoe, 2026-11-04. CLI migration completed on 2026-11-05 following the explicit request to support all tools. Approval covers the architectural direction and CLI implementation. Breaking changes are acceptable while the harness is in development. This document does not itself install capabilities or change agent permissions.

Expose engineering processes through small, automatically selected skills, and expose executable tools through one stable CLI. Keep playbooks as the canonical process definitions. Start with change review as a skill and pipeline diagnosis as a playbook backed by CLI commands. Measure their effectiveness before expanding automatic process selection.

This optimizes for predictable agent behavior, less repeated tool discovery, and lower context consumption. It costs CLI maintenance, adapter integration, and behavioral evaluation. Token savings remain a hypothesis until measured.

Implementation: the CLI migration covers every current public harness tool operation. The [checked catalog](../../harness/tools/cli/catalog.json) exposes 82 public routes across 51 tool implementations and classifies 23 additional implementation files as internal. The [command reference](../../harness/tools/cli/commands.md) lists each route, implementation and declared effects. Comparative process effectiveness and resource measurements remain separate from command coverage.

The proposed [process-step skills and document-discovery extension](process-step-skills-and-document-discovery.md) remains deferred. Completing this CLI proposal does not approve or begin that extension.

## CLI migration status

Command coverage completed on 2026-11-05. Run `tvh tools --check --json` to reproduce the source inventory; new unclassified executable files, missing implementations and duplicate command paths fail the coverage check. Every public route also has offline CLI help and contract coverage. Installation or credentials for every optional runtime are not implied by a registered route.

| Tool area | Supported CLI routes |
| --- | --- |
| Bundle and guidance | `bundle`, `context select`, density reports/duplicates/candidates, adapter checks |
| Review and findings | `review`, `findings validate`, `findings render`, `eval reviewer`, resumable `eval queue` operations |
| Verification and gates | `verify`, `project verify-config`, `checks` registry/run/code-types/secrets/keyvault/review-plan/report/install-tools, IaC/scenario/test-presence/OpenAPI/Node checks, explicit-file `code types` |
| Operational reads | `cloud read`, `sonar read`, `servicenow`, `deps`, `dev read`, ADO run diagnosis/watch/timing and PR threads |
| Operational writes and human tools | ADO PR-findings posting with existing pipeline identity and prior validation; terminal-only review-comment mining, container login and MSAL state production |
| Design and artifacts | Greenfield initialization/design checks, convention discovery, spec notes, diagrams/logo/icon lookup, frontend capture/comparison/contrast, business test plans |
| Evaluation and planning | Candidate freeze/run/rescore/login, artifact freezing/verification, brownfield run/grade, run diagnosis, usage/coverage analysis, backup grading, container image builds, native skill-selection probes and orchestration |

Declared native routes use CLI controls before `--` and native arguments after it. `--json` returns the execution envelope; `--raw` preserves native stdout for existing JSON/text pipelines. Exit mapping and effects are explicit in the catalog. Required outputs default into external evidence storage where possible. Checks requiring a changed-path list require explicit stdin scope. Missing runtimes, authentication failures, timeouts, rejected or dropped findings, and incomplete native results cannot become clean checks.

Internal libraries, provider/grader adapters, hook protocols, diagram package modules and the brownfield snapshot verification fixture are intentional private implementations. Their owning public commands or protocols are recorded in the catalog. They do not need redundant public commands. Native implementation calls may remain in CI, hooks, adapters, engine tests and source-code documentation; agent-facing process instructions use the CLI.

External-write routes retain existing authority and identity requirements. Supporting a PR-posting command does not authorize an agent to post. Human-only operations require an interactive terminal and do not capture credential exchanges in CLI logs. No blanket permission rule is added. Real optional infrastructure and credential-dependent operations are not claimed to be validated merely because routing and stubbed boundary checks pass.

The migration completion criterion is one supported CLI route for every current public operation, explicit reasons for internal exclusions, valid public command references, and passing command/coverage tests. Keep this criterion enforced as tools are added. Full workflow outcomes, native skill selection, business approval, and cost effectiveness remain separate evidence dimensions.

## Problem and current position

The harness already contains substantial process guidance, executable tools, deterministic gates, and evidence contracts. Agents still need to interpret routing prose, locate scripts, choose runtimes, and discover argument and output conventions. A documented process can therefore exist without being selected or followed consistently.

The current implementation provides a useful starting point:

- [AGENTS.base.md](../../AGENTS.base.md) contains universal rules, process routing, and concrete script invocations.
- [Playbooks](../../harness/playbooks/index.md) describe task triggers, steps, exceptions, and expected outputs.
- [Tools](../../harness/tools/index.md) implement operations across several runtimes and domains.
- [tv-review](../../adapters/tv-review.skill.md) is already a small skill adapter that directs the agent to a canonical playbook. The installer registers it for Claude Code and Copilot.
- [Context delivery](../../harness/tools/harness/context.py) selects relevant rules before edits and deduplicates unchanged guidance. Its receipt establishes selection, not that an agent read or followed every document.
- [Verification contracts](../../harness/tools/verification/index.md) distinguish executed checks, retained evidence, semantic review, and approval.

The proposal connects these components through consistent discovery and execution contracts. It follows [H.2](../../harness/rules/harness/h-2-repeated-work-moves-up.md), which moves repeated procedures into executable tools and checks.

## Proposed architecture

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Base instructions | Universal constraints and concise discovery guidance | Avoid embedding the full process and command catalog |
| Process skills | Describe when a process applies, its required inputs, and its canonical playbook | Do not duplicate rules or playbook steps |
| Playbooks | Define process sequence, judgment, exceptions, and required evidence | Keep provider-specific invocation details in adapters |
| Unified CLI | Execute deterministic operations with stable arguments and results | Preserve underlying permissions and evidence semantics |
| Hooks and CI | Deliver context and enforce applicable required checks | Do not depend on voluntary skill selection for enforcement |

The intended flow is a user request, automatic skill selection, loading the relevant playbook, CLI execution, and an evidence-backed result. Users can still invoke a skill explicitly, but routine use must not require remembering slash commands.

### Skills and canonical content

Keep process content under `harness/playbooks/`. Publish small native skill adapters through the installation mechanism for each supported agent. Extend the existing `tv-review` pattern rather than maintain separate copies of a process for each provider.

Each adapter describes a distinct task trigger, names the required inputs, links to one entry playbook, and states the expected output. Put detailed steps and supporting references in the playbook. Load additional material only when the task needs it.

Begin with change review. Skills represent engineering processes that guide judgment across several steps, such as implementation, systematic debugging, and review. Platform-specific operations such as pipeline diagnosis stay in playbooks backed by CLI commands. Do not create a skill for every task, script, or reference document. Add another skill when a broader process benefits from independent selection. This distinction reflects the owner's clarification after approval.

Use precise descriptions and proportionate process depth. A routine correction with established acceptance criteria should not trigger a discovery interview or a full design process. Ambiguous requirements and consequential design choices can require more investigation under the existing playbooks.

Automatic invocation is a behavior to evaluate, not a guarantee supplied by the file format. Verify discovery and selection separately for each supported agent and record unsupported capabilities. Where native discovery is unavailable, retain concise base-instruction routing and report the limitation. This preserves the provider-neutral direction in [ADR 0006](../adr/0006-agent-and-model-independence.md).

### CLI interface

Use `tvh` as the proposed command name, subject to checking naming and installation conflicts. Initially implement a thin dispatcher over existing scripts. Keep working implementations in their current runtimes; do not make a language rewrite a prerequisite.

Illustrative commands, unavailable until implemented:

```bash
tvh context select --repo . --changed
tvh verify --repo .
tvh review --repo . --baseline origin/main
tvh ado run diagnose --id 12345
tvh frontend capture --url http://localhost:3000
tvh doctor
```

Use domain commands where systems differ. An Azure DevOps pipeline run and a GitHub Actions run can share result fields without pretending their identifiers or capabilities are interchangeable.

The initial command contract must provide:

- Stable command help, explicit inputs, and actionable prerequisite errors. `doctor` reports available tools and supported capabilities without revealing credentials or triggering login, installation, or network operations by default.
- A documented exit convention. Propose 0 for a completed successful check or operation, 1 for a completed check with findings or failure, and 2 for invalid input or incomplete execution. Detailed results distinguish causes; an unavailable check never becomes a clean pass.
- Human-readable output and a versioned `--json` result containing command status, scope, findings or result data, and artifact references. JSON goes to stdout and diagnostic text to stderr. Do not silently truncate findings; retain complete artifacts and report output limits.
- Explicit repository, baseline, timeout, and output-directory handling where applicable. Do not guess a default branch when the operation requires a comparison baseline.
- Noninteractive execution. Missing credentials or dependencies produce instructions and an incomplete result; they do not initiate authentication or installation.
- Argument-array dispatch without shell evaluation. Diagnostic messages and finding text never become executable commands.

Reuse existing native findings and verification receipts. A common CLI result can reference these artifacts without replacing their schemas. A pipeline diagnosis result describes what was observed; it is not a verification approval. A semantic review remains separate from deterministic checks.

The CLI exposes executable operations. Processes that require agent judgment remain in playbooks. For example, a review command may execute the existing reviewer, but decisions about safe remediation and unresolved behavior still follow the review playbook.

### Permissions and enforcement

Preserve the authorization boundaries in [ADR 0004](../adr/0004-harness-scope-and-boundaries.md). Skills and the CLI do not grant approval authority or permission to mutate cloud state.

Audit hooks and installation rules before introducing the new entry point. Existing controls recognize concrete wrapper paths. A blanket allow rule for every `tvh` subcommand could permit operations that previously required separate authorization.

Classify each public command by its effects, including local writes, network access, and external mutations. Dispatch cloud reads through the current restricted wrappers and preserve their credential and redaction behavior. Local verification can execute repository build and test code, so label it as local execution rather than a read-only security boundary. Commands with external write effects retain their existing authorization requirements.

Keep required checks independent of skill selection and document retrieval. The absence of a selected rule does not waive an explicitly required check. Hooks remain guardrails; identity permissions and CI policies retain their existing enforcement roles.

## Lessons from the reference projects

[Superpowers](https://github.com/obra/superpowers) demonstrates explicit workflow triggers, systematic debugging, verification before completion, and independent review. Its [bootstrap](https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md) requires skill invocation even when applicability is very uncertain. Borrow the targeted practices, but avoid a universal invocation requirement and mandatory process depth for every task. Measure total run cost, including additional reasoning and review sessions, rather than skill file size alone.

[Matt Pocock's skills](https://github.com/mattpocock/skills) provide small, composable engineering guidance and distinguish user-invoked orchestration from model-invoked discipline. Use that packaging approach for automatic process selection. Evaluate imported instructions against our working model before adopting them. His current [TDD skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md), for example, requires confirmation of test boundaries before tests are written. The harness supplies executable checks and retained evidence alongside such guidance.

[Anthropic's source-control redesign](https://www.anthropic.com/research/redesigning-source-control) argues for programmatic operations and retrieving only the data an operation needs. Our interpretation is to apply that principle to harness commands and context delivery. Their replacement for Git addresses exceptional monorepo throughput, and their testing approach reflects that workload. This proposal retains Git, existing CI, and human approval boundaries. It does not adopt a source-control service, replace merge policy, or move required checks after merge.

These sources are design references, not dependencies to install. Their mutable branches should be recorded at exact revisions if implementation imports content.

## Alternatives and trade-offs

| Option | Benefit | Cost or limitation |
| --- | --- | --- |
| Keep prose routing and script paths | Minimal implementation work | Agents continue repeating command discovery and process selection |
| Move all playbooks into native skills | Direct discovery | Risks duplicated content and couples canonical processes to client packaging |
| Adopt a complete external process framework | Broad workflow coverage | Adds process, context, and integration costs that need separate justification |
| Small skill adapters plus a unified CLI | Reuses current guidance and tools; makes invocation consistent | Requires maintained command contracts and per-agent behavioral evaluation |

The proposed option adds consistency without introducing another orchestration framework. The implementation uses a checked local command catalog and thin dispatch. It adds no plugin system, remote execution service, or policy engine.

## Delivery and migration

1. Inventory the commands used by pipeline diagnosis and change review. Record inputs, outputs, runtimes, effects, current restrictions, and existing evidence formats. Capture baseline runs before changing routing.
2. Implement the minimal CLI entry point, help, capability diagnostics, and dispatch for those commands. Add contract tests for argument forwarding, paths containing spaces, exit/result mapping, malformed output, timeouts, and preserved restrictions.
3. Align the existing review skill with the CLI. Keep pipeline diagnosis in its playbook and commands. Verify review-skill installation and actual discovery for Claude Code and Copilot; assess Codex support separately before claiming parity.
4. Update pilot playbooks, relevant base instructions, installation rules, and hooks together. Make the CLI the supported pilot interface without compatibility aliases. Existing scripts can remain internal implementations and direct CI entry points.
5. Evaluate the pilot against the baseline. Expand to additional processes only after reviewing quality, selection reliability, and resource use. Deprecate direct script invocation in agent-facing documentation once equivalent behavior is demonstrated.
6. Completed: migrate the full public tool inventory, update agent-facing references, and check result/exit mapping and existing restrictions. Maintain exhaustive classification and route-help tests. This work is separate from adding skills; onboarding an operational command does not require creating a skill for it.

The CLI ships with the pinned harness revision. Do not auto-update it independently of its skills and playbooks. Installation must detect conflicting executables and offer an explicit path when PATH setup is unavailable. Rolling back restores the previous pinned harness revision; no compatibility layer is required.

The separate [headless Sonar proposal](headless-sonar-analysis.md) can later expose its proposed verification operation through this CLI. Neither proposal assumes that operation already exists.

## Proposed acceptance and evaluation

The following criteria separate CLI correctness from process and model evaluation:

- Natural-language review requests select the review skill without an explicit name. Operational requests use the matching playbook and commands without inventing a dedicated skill. Negative cases, such as explaining pipeline concepts or inspecting an unrelated file, do not start a review process.
- Pilot tasks use the supported commands without searching for internal script paths or reconstructing runtime invocations.
- The CLI preserves underlying findings, incomplete states, and evidence references. Missing tools, failed reads, malformed output, timeouts, and verification failures cannot report success.
- Existing restricted operations remain restricted through both the CLI and legacy entry points. No broader credential access or blanket command authorization is introduced.
- Verification evidence remains linked to the source and harness state where applicable. Required results remain incomplete when checks are missing or unavailable.
- Existing relevant deterministic tests pass. Playbook and routing changes receive the repository's applicable reviewer evaluations plus focused behavioral cases for process selection.

Compare representative tasks under equivalent agent, model, source, and harness conditions. Include an unavailable credential, a failed required check, ambiguous scope, an unrelated task, and a normal successful run. Repeat behavioral cases to expose inconsistent selection rather than relying on one demonstration.

Record task success, missed required steps, incorrect process activation, unnecessary questions, human correction effort, command-discovery calls, loaded guidance size, reported token usage, and wall time. Mark unavailable usage metrics as unknown. Report provider and adapter differences explicitly.

Adopt the pilot only when it preserves required behavior and reduces discovery effort. Set quantitative thresholds and approve the scenario set before comparison; do not choose a success threshold after seeing results. Lower token usage does not compensate for skipped verification or weaker authorization.

## Decisions requested

The architectural direction and CLI migration are approved and implemented. The process-step skills extension remains proposed. Use `tvh` with a harness-owned executable directory and target Claude Code and Copilot first. Quantitative adoption thresholds and comparative model runs remain to be agreed before claiming improved effectiveness. Use the existing architecture decision process if this becomes the long-term tooling interface. This proposal does not itself amend approved ADRs or consumer repository policies.
