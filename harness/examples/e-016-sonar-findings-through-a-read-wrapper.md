---
type: Example
title: "E-016 An agent cannot read static-analysis findings, so the user pastes or exports them by hand"
description: A read-only Sonar wrapper that lets agents fetch project issues and hotspots without exposing tokens or requiring manual exports.
example_id: E-016
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: automation-candidate
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [sonar, wrapper, token, read-only]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - id: evidence
    resource: session, 2026-10-19: fixing Reliability findings needed the issue list; the agent had no tool, no way to hold a token, and the env var set in the user's shell was invisible to the agent process until restart.
---

# Situation

Fixing code-quality findings requires the issue list from Sonar. Without a dedicated tool, developers have to manually generate tokens and run curl loops in their shell. Sharing raw tokens directly with the agent violates SEC.2.[^evidence]

# Why (verdict)

Just like [cloud-read.sh](../tools/cloud/cloud-read.sh), external reads belong in a read-only wrapper that strictly rejects state-changing calls (H.2). This keeps credentials safe and standardizes how agents fetch findings.

# Compliant pattern

`tools/sonar/sonar-read.sh <endpoint> [key=value ...]`:

- GET only, host fixed to `sonarcloud.io`, no `-X`, no body.
- Allowlist of read endpoints: `issues/search`, `hotspots/search`, `hotspots/show`, `qualitygates/project_status`, `measures/component`.
- Token from `SONAR_TOKEN` in the shell, or from the user's env file (`~/.config/harness/.env`, or `HARNESS_ENV_FILE`), which the wrapper parses itself. It is passed to curl on stdin, never printed, never an argument, never written to disk. An agent reads only `.harness/.env.example`, to tell the user which variable is missing or expired (HTTP 401) and how to renew it.
- [guard-bash.sh](../hooks/guard-bash.sh) blocks curl to Sonar and any command naming the token.
- Exit 3 with a reason when refused, as [cloud-read.sh](../tools/cloud/cloud-read.sh) does.

- Shift left: when a change touches code Sonar analyses (C#), check findings before reporting done (T.1). With the SonarQube for IDE extension installed (`sonarsource.sonarlint-vscode`), read the IDE diagnostics for the changed files first, because that is the cheapest scan. Without it, or for the project's server-side ruleset, use `sonar-read.sh issues/search` with `impactSoftwareQualities=RELIABILITY,SECURITY`. Filtering on `types=BUG,VULNERABILITY` misses Reliability findings filed as code smells (a missed `cts.Cancel()` -> `CancelAsync` finding showed this).

# Not verified

- A Sonar user token inherits the user's permissions and cannot be scoped read-only. Layer 1 (a dedicated reader account) is a human decision; the wrapper is layer 2 only.
- Whether `SONAR_TOKEN` belongs in the shell profile or in a per-session export. It is in `~/.zshrc` today.
- Whether the harness should also carry a playbook (`fix-sonar-findings.md`) or wait for a second use.

[^evidence]: Sonar findings session, 2026-10-19
