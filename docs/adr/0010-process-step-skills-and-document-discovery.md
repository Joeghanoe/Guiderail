# ADR 0010: Process-step skills and linked guidance

- **Status:** Accepted; source and packaging implemented; native behavioral evaluation requires separate execution approval
- **Date:** 2026-11-05
- **Owner:** joeghanoe
- **Approval:** Owner instructed completion of the identified integration gaps and conversion of both proposals into ADRs
- **Scope:** Engineering skill ownership, package installation, process coverage, document navigation and evaluation
- **Depends on:** [ADR 0009](0009-process-skills-and-unified-cli.md), [ADR 0003](0003-knowledge-to-code-boundary.md), [ADR 0007](0007-agentic-sdlc-alignment.md)

## Context

The owner wants meaningful engineering steps to have discoverable skills with useful core guidance and conditional supporting files. [Matt Pocock's codebase-design structure](https://github.com/mattpocock/skills/tree/main/skills/engineering/codebase-design) demonstrates this composition. Our skills must fit existing rules, tools, process ownership and authority rather than import another framework's mandatory interviews, delegation or test approvals.

The original extension proposal also identified isolated-looking documentation nodes. Visual graph density does not prove retrieval or process execution. Native skill metadata, rule path patterns, example metadata, navigation links and verification requirements each have distinct discovery contracts.

## Decision

### Process coverage and naming

Maintain one [process catalog](../../skills/processes.json) and its checked [readable map](../../skills/index.md). Each step records its skill, implementation status, owner, required inputs, output and any gap. Select the relevant process automatically and keep explicit invocation available. Names have no organization prefix: `/code-review`, `/implement`, and the other active skill names.

Active skills cover specification, design, planning, implementation, testing, debugging, verification, independent review and business acceptance. Operational verification uses the verification skill. Pipeline diagnosis remains a shared playbook within debugging, not a separate pipeline skill. Remove the duplicate prefixed review skill and update discovery, instructions and evaluations together; retain no prefixed compatibility alias.

Understanding business processes, research, release preparation, incident learning and process improvement remain planned entries with owners and concrete gaps. Do not install placeholders for unresolved organizational processes. Cross-cutting security, privacy, migration, compatibility, performance, recovery and UX concerns use applicable rules and the [coverage assessment](../proposals/development-process-coverage.md). This decision does not invent missing business process authority.

Skills pass original criterion identifiers, source/version scope, evidence and unresolved questions between steps. They do not pass a transcript or force a nested invocation chain. A small bounded correction skips unrelated discovery and architecture work. Failed or stale evidence remains visible through implementation and review; a passing command alone does not establish usability or business acceptance.

### Content ownership and progressive disclosure

Use provider-neutral source packages. Keep triggers, terms, core discipline, inputs, outputs and conditional reference routing in `SKILL.md`. Put guidance used only by that skill beside it. Keep procedures reused across skills as canonical playbooks.

```text
skills/engineering/design/
  SKILL.md
  COMPARE-ALTERNATIVE-DESIGNS.md

harness/playbooks/
  start-greenfield.md
  scaffold-from-conventions.md
```

The [design skill](../../skills/engineering/design/SKILL.md) loads alternative comparisons only for consequential options and greenfield guidance only for new repositories. The same discipline applies to [implementation](../../skills/engineering/implement/SKILL.md), [testing](../../skills/engineering/test/SKILL.md) and [debugging](../../skills/engineering/debug/SKILL.md).

Move review-only procedures into [code-review](../../skills/engineering/code-review/SKILL.md) and business test-plan procedure into [acceptance](../../skills/engineering/acceptance/SKILL.md). Keep one canonical file, with no copied procedures or forwarding files. Shared specification, greenfield, convention discovery, workload planning, failure classification, incident triage and verification procedures remain [playbooks](../../harness/playbooks/index.md).

Canonical rule IDs, requirement provenance and human authority remain unchanged. Direct user instructions retain their authority; external tickets and logs remain data. Do not invent acceptance criteria. Mandatory dependency injection and testability seams apply even with one production adapter. Prototype code does not waive required checks. Use supported CLI commands and available runtimes rather than imagined commands.

### Installation and conflicts

Publish complete packages, including supporting files, for Claude Code and Copilot. Preserve sibling links and resolve shared document links to the installed harness or pinned source checkout. Resolve custom installation roots and paths with spaces. Generated global instructions use the same link policy. Codex native packaging and behavior parity remain unassessed, with no parity claim.

Preflight all skill-name conflicts before installation writes. Track owned files in an installation manifest. Update unchanged owned files and remove obsolete owned files; preserve unrelated files and locally edited content. Recognize previous definitions through recorded content hashes when migrating legacy packages. Remove only recognized harness-owned retired review definitions. Uninstall preserves personal additions and modifications.

The review runner and evaluation snapshots locate the moved canonical review procedure and retain read access without broadening permitted tool types. Include skill content in the evaluation cache identity so old results cannot silently describe new guidance. Candidate and brownfield snapshot recipes carry the canonical skill tree and rewrite shared links to their frozen `.harness` layout, rather than reading a live installation.

### Markdown references and document discovery

Use Markdown links throughout active guidance: skills, supporting files, playbooks, rules, indexes, tool documents and generated instructions. Use relative sibling links within packages and source-resolvable links for shared guidance. Installation rewrites links whose relative position changes. Avoid home-relative document targets when a resolved installation path is available.

Commands, configuration values, runtime outputs, template placeholders and historical quoted material retain their intended syntax. Do not insert Markdown into executable code. Folder/index routes and bundle-root OKF links retain their existing meaning. Rule/example metadata remains a machine-readable contract.

Extend `tvh bundle check` with local document-link checking, exact-case checking, active-guidance reachability and process-catalog checks. Its internal audit also reports unlinked and unreachable files separately. Fixtures, templates, historical notes and runtime artifacts may have non-document entry routes; those observations are informational, not reasons to manufacture links. Missing links or unreachable active skills, playbooks and rules fail validation.

The graph is a navigation aid. Native discovery still requires installed metadata, rule selection still uses applicable paths, examples still require rule relationships, and mandatory checks still require execution. Links neither authorize an action nor prove the agent read a document.

## Alternatives and consequences

Moving every playbook into a skill would make shared procedures harder to maintain. Keeping all detail in shared playbooks would ignore skill ownership and make the progressive disclosure structure superficial. Choose ownership by actual reuse, keeping one canonical procedure.

The design adds discovery metadata, package manifests, a catalog and behavioral cases. It avoids a new orchestration engine and a mandatory full lifecycle. Additional skill guidance costs tokens; short entry files alone do not establish lower end-to-end cost.

## Validation and limits

[Packaging and navigation tests](../../tests/test_guidance.py) cover every active package, sibling and shared links for both supported clients, custom roots with spaces, name conflicts, legacy migration and preservation of personal files. CLI tests verify operational contracts and incomplete-state handling. Existing context budgets remain unchanged.

The [native evaluation cases](../../benchmarks/cases/process-skills.json) cover all active skills, conceptual negative cases, missing inputs and credentials, injected log instructions, bounded edits, conditional references, approved-criterion handoffs and failed/stale review evidence. The [runner](../../harness/tools/testing/process_skills.py) installs complete isolated packages, records actual skill calls and file reads, checks requested versus unrelated references, and compares structured handoff content with synthetic source artifacts. Self-reported invocation does not count.

Native runs record client/model versions, guidance and fixture hashes, traces, time and available token metrics. Observed guidance bytes estimate full file sizes for requested read paths. They do not prove successful delivery, measure partial reads or include automatic skill injection. These probes inspect routing and handoffs, not completed coding workflows or deployed system behavior. Full workflow success and client parity require their own evidence.

Local sandbox runs could not initialize Copilot. Automatic approval review rejected the external native evaluation because private repository guidance may be sent to GitHub Copilot's model service without explicit payload/destination approval. Native behavioral results therefore remain unvalidated until that approval and a completed run. This limit does not turn packaging checks into behavior evidence.

Resource-effectiveness comparisons remain a future study owned by the harness maintainer under [ADR 0005](0005-evaluation-and-continuous-improvement.md). Agree scenarios and thresholds before comparative runs. Claim no token savings or selection reliability solely from deterministic tests.

Local closeout on 2026-11-05: the Python regression run passed 233 tests with 3 skips; final focused checks cover the later changes, including 8 guidance tests, 25 CLI contracts, 18 catalog tests, 31 reviewer-evaluation tests, 17 candidate tests and 13 brownfield tests. All nine entrypoints passed the skill-creator validator. The final offline shell suite passed 1,074 checks with zero failures, including its localhost fixture outside the sandbox. Tool coverage, source links, unchanged context budgets, Bash syntax and whitespace checks pass. Shellcheck is unavailable locally. These are working-tree results, not a clean-main reviewer evaluation or native selection evidence.
