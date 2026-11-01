---
type: Example
title: "E-021 A growing service groups files by responsibility, then by external system"
description: Organize growing services by business capability and external adapters rather than dumping everything into flat Models and Services folders.
example_id: E-021
rule: /rules/code/code-8-dependencies-point-inward.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:28:57Z }
tags: [code, design, folders, dependency-direction]
eval_tree: true
generated: { by: openai/codex, at: 2026-10-30T00:00:00Z }
sources:
  - id: evidence
    resource: greenfield evaluation runs and direct maintainer feedback, 2026-10-30
---

# Situation

As a service grows, handlers, contracts, and third-party integrations are dumped into generic `Models/` and `Services/` folders, with global `Interface/` and `Shared/` dumping grounds.

# Why (verdict)

Flat, technical folders (`Models/`, `Services/`) obscure domain ownership and dependency direction (CODE.8). Maintainers cannot tell which components change together or where external boundaries lie. Group code by business capability (e.g., `Processing`) and encapsulate third-party integrations behind dedicated adapter boundaries (`Adapters/<System>`).

# Compliant pattern

This is one valid layout, not a mandatory set of folder names. `Processing` owns the use case. `Adapters` owns the external boundary and groups implementations by external system. Contracts and domain values no longer share one undifferentiated `Models` folder.

## Good example

```text
src/WorkProcessor/
  EntryPoints/
    ProcessWorkFunction.cs
  Contracts/
    ProcessWorkRequest.cs
    ApiResponse/
      ProcessWorkResponse.cs
  Domain/
    WorkItem.cs
    WorkItemAttachment.cs
    WorkItemComment.cs
  Processing/
    Abstractions/
      IExternalSystem.cs
    Handlers/
      ProcessWorkHandler.cs
    NotificationService.cs
    ExternalSystemResolver.cs
    SynchronisationService.cs
  Adapters/
    SystemA/
      SystemAAdapter.cs
    SystemB/
      SystemBAdapter.cs
  Extensions/
    HttpClientExtensions.cs
  Program.cs
```

`EntryPoints` depends on `Processing`. `Processing` owns the external-system abstraction. Implementations under `Adapters` depend inward on that abstraction, and `Program.cs` is the only place that selects them. `Contracts` and `Domain` do not depend on entry points, application services or adapters.

## Bad example

```text
src/WorkProcessor/
  Models/
    WorkItem.cs
    ProcessWorkRequest.cs
    SystemAResponse.cs
    ProcessWorkResponse.cs
  Services/
    ProcessWorkHandler.cs
    NotificationService.cs
    SynchronisationService.cs
    SystemAAdapter.cs
    SystemBAdapter.cs
    ExternalSystemResolver.cs
    Interface/
      IExternalSystem.cs
    Shared/
      AdapterHelpers.cs
  ProcessWorkFunction.cs
  Program.cs
```

# Not verified

A human must approve the convention before it becomes stable precedent.
