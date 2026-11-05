---
type: Example
title: "E-019 A pure rename does not raise major findings"
description: "A reviewer abstains from raising major findings when a PR only renames an already well-named file without altering behavior."
example_id: E-019
rule: /rules/code/code-3-names-say-what-it-is-for.md
eval_rule_id: CODE.3
eval_behavior: rename
verdict: compliant
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-20T19:47:15Z }
tags: [review, abstention, rename]
example_file: src/TaskProcessor.cs
eval_before_file: src/TaskProcessorOld.cs
eval_after_file: src/TaskProcessor.cs
generated: { by: copilot/agent, at: 2026-10-20T19:05:00Z }
---

# Situation

A file is renamed to match its contained type without any code modifications.

# Why (verdict)

Reviewers should distinguish pure renames from logic changes. When the target file and type names are already clear, the reviewer should abstain from flagging major issues ([CODE.3](../rules/code/code-3-names-say-what-it-is-for.md)).

## Good example

```csharp
namespace Example;

public sealed class TaskProcessor
{
}
```

## Bad example

```csharp
namespace Example;

public sealed class X
{
}
```
