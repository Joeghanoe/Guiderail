---
type: Example
title: "C-NNN Local static analysis must cover files without opening them in an editor"
description: Propose a headless local analysis capability using Sonar Roslyn analyzers and ESLint, with explicit coverage and verification evidence.
example_id: C-NNN
rule: /rules/harness/h-2-repeated-work-moves-up.md
verdict: automation-candidate
status: draft
tags: [feedback, sonar, static-analysis, dotnet, eslint, automation]
generated: { by: openai/codex, at: 2026-11-04T00:00:00Z }
sources:
  - id: evidence
    resource: "User request, 2026-11-04: replace reliance on the SonarLint VS Code extension because opening files to obtain findings interrupts the workflow."
  - id: upstream
    resource: https://github.com/SonarSource/sonarlint-vscode
---

# Situation

An agent needs static-analysis findings for local edits. The user reports that the IDE extension requires opening files to obtain those findings. Opening each file adds manual work and makes verification depend on editor state.[^evidence]

The existing Sonar reader retrieves published server findings. It does not analyze the working tree, so its results cannot establish that an uncommitted change passes local analysis.

# Why (verdict)

H.2 supports replacing this repeated interaction with a deterministic command. T.1 requires evidence for the checked code; an empty IDE diagnostics list is insufficient when the files were never analyzed. CODE.6 favors existing analyzer engines over recreating Sonar rules.

This draft proposes a change to the IDE-first workflow in human-reviewed E-016 and T.1. E-016 remains authoritative until review. Preserve its read-only server wrapper and SEC.2 credential handling. The proposed local runner needs no Sonar token and complements the server reader.

# Compliant pattern

Provide a local command that reads files from disk and analyzes the declared projects independently of the editor. For C#, run `SonarAnalyzer.CSharp` during a build, with rule severities configured in `.editorconfig` or `.globalconfig`. For JavaScript and TypeScript, run the repository's ESLint with `eslint-plugin-sonarjs` and the required parser/type configuration. StyleCop is an optional C# style analyzer, not a substitute for Sonar's bug and maintainability rules.

Record the engine versions, configuration, actual scope, findings and failures. Missing analyzers, excluded requested files, build errors or missing type information must not become a clean result. Local analysis does not establish a server quality gate or full SonarQube rule parity.

The [tool implementation proposal](../docs/proposals/headless-sonar-analysis.md) specifies the command, adapters, evidence, adoption and acceptance checks.

## Good example

```text
agent: Analyze the declared C# project with its configured Sonar analyzer.
runner: Analyzes the project's compiler inputs, including files closed in the IDE.
runner: Reports rule IDs, locations, coverage and execution status.
agent: Fixes the findings and reruns analysis before reporting local verification.
```

## Bad example

```text
agent: Reads an empty IDE Problems list without checking analysis coverage.
agent: Reports that all changed files pass Sonar analysis.
```

# Not verified

The runner is proposed, not implemented or registered as an available capability. No consumer dependencies, quality profiles, IDE settings or CI gates have changed. Real-engine coverage, runtime cost and configuration compatibility require the pilot checks in the proposal.

[^evidence]: User request to capture editor-independent Sonar analysis through the feedback mechanism.
