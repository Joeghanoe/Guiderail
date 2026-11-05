---
type: Gate
title: "C# declaration layout (CODE.5)"
description: The existing Roslyn checker evaluates added or changed declarations against a pinned baseline and retains JSON evidence for each selected conditional configuration.
tool: harness/tools/verification/verify.py code-types, wrapping harness/tools/code/CheckTypes.csproj
owner: team:teamvalue-aicoe
status: stable
tags: [code, dotnet, verification]
---

# Coverage

The full verify template invokes the runner locally. The reusable PR pipeline runs it independently of guidance selection against the PR merge base, so a custom verify command cannot silently omit it. Existing consumer installations change only when they update their pinned harness/template.

The runner discovers staged, unstaged and untracked C# changes from Git. It materializes baseline versions of the inspected files and runs the existing syntax checker. Unchanged declarations remain inherited evidence; added or changed violations fail. The executable checker and its regression fixtures define the structural exceptions; this gate does not maintain a second definition of them.

# Configuration

Local baseline defaults to HEAD. Set `HARNESS_BASE_REF` for a branch comparison. The pipeline supplies the pinned PR merge base. For conditional code, declare supported configurations through `CODE5_SYMBOLS`, separated by semicolons, or pipeline `code5Symbols`. Each configuration is checked independently. Missing symbols on a conditional file is an error. `--audit` explicitly inspects all current files rather than evaluating a change.

# Evidence and failure behavior

Receipts, logs and checker JSON remain outside the source repository. Exit 0 means the inspected structural scope passed or contains no C# changes, exit 1 means introduced findings, and exit 2 means verification could not complete. The receipt records scope, baseline, symbols, tool hashes, SDK, source hashes and inherited findings. Required errors remain incomplete; they do not become compliance.

# Blind spots

Syntax cannot establish cohesive responsibility, private-helper single-user ownership, semantic correctness or other languages. Configuration coverage is only the declared symbol sets. Textual baseline comparison can treat formatting changes as touched declarations. Untracked-state provenance uses metadata rather than reading arbitrary credential files; receipts are evidence artifacts, not signed attestations.

# Complementary review

[CODE.5](../rules/code/code-5-one-responsibility.md) responsibility uses the independent reviewer and its rubric. Consumer functional tests, build and other required checks still run. This gate does not alter example verdicts or reviewer thresholds.
