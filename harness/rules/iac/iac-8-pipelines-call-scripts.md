---
type: Rule
title: "IAC.8 Pipelines call scripts; they do not contain them"
description: Anything longer than a line or two is a script file in the repo that can be run and tested locally, and the pipeline step calls it.
rule_id: IAC.8
principle: /principles/p-06-automation-by-default.md
tags: [iac, pipelines, testing]
applies_to: ["**/*.yml", "**/*.yaml"]
enforced_by: [review]
severity: minor
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- An inline `script:`, `powershell:` or `bash:` block is a call or at most a few lines. Longer logic is a script file next to the pipeline, which takes its inputs as parameters.
- The script runs on a developer machine with the same arguments, so it can be tested without a pipeline run.
- Build and deploy steps run on the cheapest agent that does the job (`ubuntu-latest` unless a step needs Windows, and then a comment says which).
- Triggers say what they trigger on: CI on pull requests, deployment on the main branch only.

# Boundary

A one-line command (`dotnet test`, `az bicep build`) stays inline.

# Related guidance

This rule applies [P6 Automation by Default](../../principles/p-06-automation-by-default.md).

Worked examples:

- [E-013 A pipeline step calls a script; it does not contain one](../../examples/e-013-pipelines-call-scripts.md) (violation).
