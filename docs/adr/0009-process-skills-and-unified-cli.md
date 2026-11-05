# ADR 0009: Process skills backed by one harness CLI

- **Status:** Accepted; CLI implementation complete
- **Date:** 2026-11-05
- **Owner:** teamvaluegroup
- **Approval:** Architectural direction and implementation approved on 2026-11-04; full public tool coverage requested subsequently
- **Scope:** Public harness command invocation, evidence and native process integration
- **Depends on:** [ADR 0004](0004-harness-scope-and-boundaries.md), [ADR 0005](0005-evaluation-and-continuous-improvement.md), [ADR 0006](0006-agent-and-model-independence.md), [ADR 0007](0007-agentic-sdlc-alignment.md)
- **Extended by:** [ADR 0010](0010-process-step-skills-and-document-discovery.md) for skill content ownership and document discovery

## Context

The repository already has rules, playbooks, executable tools and verification contracts. Agents repeatedly had to discover script locations, runtimes and argument conventions. Documenting a process did not establish that the agent selected or followed it.

The owner approved breaking changes while the harness is in development and required every public tool operation to have a supported CLI route. Pipeline diagnosis remains an operational procedure backed by commands, not a dedicated skill.

## Decision

Use `tvh` as the supported interface for public harness operations. Keep implementations in their existing runtimes behind thin argument-array dispatch. Maintain a checked command catalog, command help and explicit classification of private implementations. Do not add a plugin system, remote execution service or workflow engine.

The [catalog](../../harness/tools/cli/catalog.json) exposes 82 public routes across 51 public implementations and classifies 24 implementation files as internal. The [command reference](../../harness/tools/cli/commands.md) records their effects and owning routes. Run the inventory check whenever tools change:

```bash
tvh tools --check --json
```

Libraries, provider/grader adapters, hook handlers, package modules and snapshot fixtures remain private with an explicit reason. Adding a public operation requires its route and coverage classification. Bootstrap installation and CI wiring retain their own entry points.

### Command and evidence contract

Use domain commands with explicit scope. An Azure DevOps run and a GitHub Actions run do not share identifiers merely because result fields overlap.

```bash
tvh context select --repo . --changed --baseline <established-baseline>
tvh verify --repo .
tvh review --repo . --baseline <target-ref> --engine <authorized-engine>
tvh ado run diagnose --organization <organization> --project <project> --id <run-id>
tvh frontend capture --url http://localhost:3000
tvh doctor
```

Declared native routes take CLI controls before `--` and native arguments after it. `--json` returns a versioned execution envelope; `--raw` preserves complete native stdout for existing pipelines. Human previews are bounded and full logs remain in external evidence storage. Existing findings and verification receipt schemas retain their contracts.

Exit 0 means completed success, 1 means a completed check found failure or findings, and 2 means invalid input or incomplete execution. Missing runtimes, unavailable credentials, malformed output, dropped findings, timeouts and missing artifacts cannot become clean results. An operational read completing does not establish pipeline health or root cause.

Provide explicit baseline, repository, timeout and output handling. Never guess the default branch. Dispatch argument arrays without shell evaluation. Diagnostic text and findings never become commands. `doctor` and help inspect local capabilities without logging in or installing dependencies.

### Discovery, permissions and installation

Use automatically discoverable engineering skills for process judgment and the CLI for deterministic operations. Native selection supports ordinary requests without requiring slash commands. Required checks remain enforced independently of voluntary skill selection. [ADR 0010](0010-process-step-skills-and-document-discovery.md) defines where skill-owned and shared guidance lives.

Classify command effects separately: local execution, artifact writes, network reads, installations and external writes. Retain restricted cloud and service wrappers, identity boundaries and redaction. A route for posting findings does not authorize posting. Human-only login and state-production tools require an interactive terminal and reject credential capture. Install no blanket `tvh` allow rule.

Ship the CLI with the pinned harness revision. Installation detects executable conflicts, supplies an explicit executable path and does not edit shell profiles. Rollback uses the previous pinned revision; no compatibility aliases are required. Native implementation calls may remain in hooks, CI and engine tests; agent-facing instructions use the CLI.

## Alternatives and consequences

| Option | Benefit | Cost |
| --- | --- | --- |
| Keep prose routing and direct scripts | No migration | Repeated discovery and inconsistent command contracts |
| Import a complete process framework | Broad ready-made coverage | Extra context, workflow assumptions and integration cost |
| Thin CLI plus focused skills | Reuses tools and evidence while standardizing invocation | Catalog, packaging and behavioral evaluation must be maintained |

Choose the thin CLI and focused skills. It optimizes predictable invocation and preserves existing restrictions. Lower context consumption and token savings remain hypotheses until comparative evaluation establishes them.

[Superpowers](https://github.com/obra/superpowers) informed targeted workflow triggers, systematic debugging and verification. [Matt Pocock's skills](https://github.com/mattpocock/skills) informed process-oriented progressive disclosure. Our interpretation of [Anthropic's source-control work](https://www.anthropic.com/research/redesigning-source-control) is to retrieve only the information a programmatic operation needs. These references do not justify adopting their whole frameworks or replacing Git and merge policy. No external skill package is installed by this decision.

## Implementation and validation

All current public operations have routes. Inventory and offline help checks enforce ongoing coverage. CLI tests exercise paths with spaces, argument forwarding, stdin scope, exit mapping, raw output, wrapper refusals, missing outputs and interactive boundaries. Real credential-dependent services are not proven by routing or stubs.

The [CLI contract](../../harness/tools/cli/index.md), [CLI tests](../../tests/test_cli.py) and [catalog tests](../../tests/test_cli_catalog.py) record implementation details. Skill selection, completed workflow outcomes, human acceptance and resource efficiency remain separate evidence dimensions under [ADR 0010](0010-process-step-skills-and-document-discovery.md).

No improved effectiveness or token-cost claim is approved. Before a comparative study, the owner must agree scenarios and thresholds and record equivalent client, model, source and harness conditions. Measure task outcomes, missed requirements, unnecessary activation, correction effort, loaded guidance, tokens and time; keep unavailable metrics unknown. This study is a future measurement task, not an unfinished public-tool migration.
