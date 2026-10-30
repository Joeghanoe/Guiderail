---
type: Example
title: "E-021 A growing service groups files by responsibility, then by external system"
description: Split catch-all Models and Services folders into named responsibilities, with external-system adapters kept behind one capability boundary.
example_id: E-021
rule: /rules/code/code-8-dependencies-point-inward.md
verdict: violation
status: draft
tags: [code, design, folders, dependency-direction]
generated: { by: openai/codex, at: 2026-10-30T00:00:00Z }
sources:
  - id: evidence
    resource: greenfield evaluation runs and direct maintainer feedback, 2026-10-30
---

# Situation

A service starts with a few models and services. It later gains handlers, API clients and several external-system
implementations. Every new class still goes directly into `Models/` or `Services/`, while interfaces
move into a global `Interface/` folder and reusable-looking code moves into `Shared/`.

# Why (verdict)

The flat folders identify C# type categories, not ownership or dependency direction. A maintainer cannot tell
which files change together, which models form the external contract, or whether adapter code may call an
application handler directly. `Interface/` and `Shared/` make the problem worse because their names place no
limit on what they may contain.

Keep the amount of structure proportional to the code. A small service does not need a folder per file. Once
separate responsibilities exist, name them and group implementations under the capability they implement.
The repo's `AGENTS.md` records the exact layout and allowed dependencies.

# Compliant pattern

This is one valid layout, not a mandatory set of folder names. `Processing` owns the use case. `Adapters`
owns the external boundary and groups implementations by external system. Contracts and domain values no longer share
one undifferentiated `Models` folder.

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

`EntryPoints` depends on `Processing`. `Processing` owns the external-system abstraction. Implementations under
`Adapters` depend inward on that abstraction, and `Program.cs` is the only place that selects them. `Contracts`
and `Domain` do not depend on entry points, application services or adapters.

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

The reviewer evaluation runner writes each example code block to one file, so it cannot reproduce these two
directory trees. This draft records the maintainer's layout feedback as reviewer context. A human must approve
the convention before it becomes stable precedent.
