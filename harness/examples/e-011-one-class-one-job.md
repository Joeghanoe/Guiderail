---
type: Example
title: "E-011 A health endpoint is its own class, and the client decides what its response means"
description: Health endpoints belong in dedicated classes, and client services interpret their own upstream health status.
example_id: E-011
rule: /rules/code/code-5-one-responsibility.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [design, health]
example_file: src/PartnerService.cs
eval_context_files: [src/HealthFunctions.cs]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on class and file layout, responsibility of the service class and separated deployment files (mined 2026-10-18)
---

# Situation

A connector service bundles health check endpoints inside business function classes and passes raw ping responses out to callers.

# Why (verdict)

Health checks and business functions change for completely different reasons. Mixing them violates single responsibility ([CODE.5](../rules/code/code-5-one-responsibility.md)). Furthermore, the client service that communicates with a partner dependency knows how to interpret partner health—it should not force callers to parse raw response payloads.

# Compliant pattern

## Good example

```csharp
public sealed class PartnerService(HttpClient http) : IPartnerService
{
    public async Task<HealthResult> HealthAsync(CancellationToken ct)
    {
        using var response = await http.GetAsync("ping", ct);
        return response.IsSuccessStatusCode ? HealthResult.Healthy : HealthResult.Unhealthy("ping failed");
    }
}
```

The `HealthFunctions` entry point lives separately in `src/HealthFunctions.cs`.

## Bad example

```csharp
public sealed class PartnerService(HttpClient http) : IPartnerService
{
    public Task<HttpResponseMessage> PingAsync(CancellationToken ct) => http.GetAsync("ping", ct);
}

public sealed class PartnerFunctions(IPartnerService partner)
{
    [Function(nameof(CreateContact))]
    public Task CreateContact(/* ... */) => Task.CompletedTask;

    [Function(nameof(Health))]               // unrelated to creating contacts
    public async Task<IActionResult> Health([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req,
        CancellationToken ct)
    {
        var response = await partner.PingAsync(ct);     // the function decides what the response means
        return new OkObjectResult(response.StatusCode);
    }
}
```

# Not verified

Written for this example in neutral names. The status-code part of the good example is the subject of E-014.
