---
type: Example
title: "E-107 The health function and the event publisher are copied into every connector"
description: Seven connectors carry the same health function and event publisher service, differing only in namespace; the shared package exists but only one connector uses it.
example_id: E-107
rule: /rules/code/code-5-one-responsibility.md
verdict: violation
status: draft
tags: [duplication, shared-code]
example_file: src/HealthFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-05/HealthCheckFunctions.cs#L1-L112
  - id: evidence-2
    resource: hub-conn@src/connector-06/Services/EventPublisherService.cs#L1-L52
  - id: evidence-3
    resource: hub-conn@src/connector-04/Program.cs#L12-L30
---

# Situation

Each connector is a separate function app. Six of them contain a `HealthCheckFunctions.cs` that is identical
to the others apart from the namespace, and an `EventPublisherService.cs` that wraps the event publisher with at
most a few lines of difference. One connector instead calls two extension methods from a shared package
(`AddConnectorDefaults`, `AddEventPublisher`) and writes neither class.[^evidence]

# Why (verdict)

CODE.5 says a shared helper has a shared home, not a copy per project. A fix to the health mapping or to how a
failed publish is reported has to be made seven times; the copies drift (the publisher copies already differ in
how they report an error). When the shared package exists, a new connector uses it. When a copy is touched, move
it to the package rather than editing the copy; a new shared abstraction still needs the owner's decision, so
state the assumption in the change.

# Compliant pattern

## Good example

```csharp
// Program.cs of a connector: only what is specific to this connector is written here.
worker.Services.AddConnectorDefaults<ConnectorOpenApiOptions>();
worker.Services.AddEventPublisher();
worker.Services.AddConnectorHealthChecks(context.Configuration, health => health
    .AddEventPublisherCheck()
    .AddCheck<VendorHealthCheck>("vendor"));
```

## Bad example

```csharp
// Each connector, again:
public class HealthCheckFunctions(HealthCheckService healthCheckService, TelemetryClient telemetryClient, ILogger<HealthCheckFunctions> logger)
{ /* 100 identical lines */ }

public class EventPublisherService(EventGridPublisherClient client) : IEventPublisherService
{ /* publish + a Health() that sends a test event */ }
```

# Not verified

Whether the shared package is stable enough for the other connectors was not checked. Its own tests were not run.

[^evidence]: duplicated files across connector projects
