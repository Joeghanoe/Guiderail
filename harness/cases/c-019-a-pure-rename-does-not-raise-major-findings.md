---
type: Case
title: "C-019 A pure rename does not raise major findings"
description: "A reviewer abstains from major findings when a change only renames a well-named source file."
case_id: C-019
rule: /rules/code/code-3-names-say-what-it-is-for.md
eval_rule_id: CODE.3
eval_behavior: rename
verdict: compliant
status: stable
verified: { by: human:joeghanoe, at: 2026-10-20T19:47:15Z }
tags: [review, abstention, rename]
example_file: src/TaskProcessor.cs
eval_before_file: src/TaskProcessorOld.cs
eval_after_file: src/TaskProcessor.cs
generated: { by: copilot/agent, at: 2026-10-20T19:05:00Z }
---

# Situation

A source file is renamed to match the type it already contains; the code itself does not change.

# Why (verdict)

The reviewer should distinguish a rename from a behavioral change and abstain from major findings when the
renamed file and its type are clearly named.

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
