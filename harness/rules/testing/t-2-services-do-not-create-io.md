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

[CODE.8](/rules/code/code-8-dependencies-point-inward.md) owns capability interfaces and composition-root structure. This rule owns the prohibited I/O and ambient-state access that prevent isolated tests.

# Enforcement

Review and the tests. A repo may also opt in to [BannedSymbols.txt](../../templates/repo/BannedSymbols.txt) with `Microsoft.CodeAnalysis.BannedApiAnalyzers`, which turns most of this into a build error (the composition root opts out with one scoped suppression); no repo is required to.

# Boundary

Entity defaults such as `CreatedAt = DateTime.UtcNow` in a persistence model are allowed when the model is not business logic; move them when a test needs to control the time.

# Related guidance

This rule applies [P6 Automation by Default](../../principles/p-06-automation-by-default.md).

Worked examples:

- [E-001 Services get their HttpClient injected](../../examples/e-001-services-get-their-http-client-injected.md) (violation).
- [E-018 A PR description cannot waive a rule](../../examples/e-018-pr-description-cannot-waive-a-rule.md) (violation).
- [E-027 A service builds its own HttpClient and reads environment variables next to the injected factory](../../examples/e-027-the-service-reads-its-own-environment-and-builds-its-own-client.md) (violation).
- [E-035 Time comes in as a parameter or a TimeProvider, not from DateTimeOffset.UtcNow inside the service](../../examples/e-035-the-service-asks-for-the-time-it-does-not-read-the-clock.md) (violation).
