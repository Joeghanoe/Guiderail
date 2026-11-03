---
type: Gate
title: "Banned API analyzer (T.2)"
description: Optional. Microsoft.CodeAnalysis.BannedApiAnalyzers with BannedSymbols.txt turns T.2 violations into build errors.
tool: Microsoft.CodeAnalysis.BannedApiAnalyzers 3.3.4, rule RS0030, rule set harness/templates/repo/BannedSymbols.txt
owner: team:teamvalue-aicoe
status: stable
tags: [testing, dotnet]
---

# Scope

Optional. A repo opts in by copying `harness/templates/repo/Directory.Build.props` and `BannedSymbols.txt`; the harness does not scaffold or require them, and `design-check` does not look for them.

# Coverage

Direct use of `HttpClient` constructors, `Environment.GetEnvironmentVariable`, and `DateTime`/`DateTimeOffset` `Now`/`UtcNow` in .NET projects that import `Directory.Build.props`.

# Blind spots

Clients created through other SDK constructors (`new BlobServiceClient(...)`), reflection, configuration read through `IConfiguration` inside business logic, and projects that do not import the props file.

# Complementary checks

AI review against T.2; unit tests that must run without a network.

# Failure behaviour

Build error RS0030; the project verify and the PR fail.

# Exception route

One scoped `#pragma warning disable RS0030` with a reason, in the composition root only. Anything wider is a boundary example with a requirement, an owner and `stale_after`.

# Refresh trigger

A new analyzer version, a new banned symbol, or a T.2 change.
