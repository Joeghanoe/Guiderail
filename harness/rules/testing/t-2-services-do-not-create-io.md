---
type: Rule
title: "T.2 Services do not create their own I/O"
description: HttpClient, configuration, clock and file system come in through dependency injection, so a service can be tested without a network.
rule_id: T.2
principle: /principles/p-06-automation-by-default.md
tags: [testing, testability, dotnet]
applies_to: ["**/*.cs"]
enforced_by: [gate:/gates/banned-api-analyzer.md, review]
severity: major
status: stable
---

# Rule

Outside the composition root (`Program.cs`, `Startup.cs`), code does not:

- construct `HttpClient`, an SDK client or a `DbContext` (use `IHttpClientFactory`, typed clients, DI);
- read `Environment.GetEnvironmentVariable` or `ConfigurationManager` (use options, validated on start);
- read `DateTime.Now`, `DateTime.UtcNow` or `DateTimeOffset.UtcNow` (use `TimeProvider`);
- touch the file system directly when the data could come from a stream or an interface.

[CODE.8](/rules/code/code-8-dependencies-point-inward.md) owns capability interfaces and composition-root
structure. This rule owns the prohibited I/O and ambient-state access that prevent isolated tests.

# Enforcement

Review and the tests. A repo may also opt in to `harness/templates/repo/BannedSymbols.txt` with
`Microsoft.CodeAnalysis.BannedApiAnalyzers`, which turns most of this into a build error (the composition root opts
out with one scoped suppression); no repo is required to.

# Boundary

Entity defaults such as `CreatedAt = DateTime.UtcNow` in a persistence model are allowed when the model is
not business logic; move them when a test needs to control the time.
