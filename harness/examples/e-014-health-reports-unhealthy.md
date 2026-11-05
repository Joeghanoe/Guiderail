---
type: Example
title: "E-014 Unhealthy is not a 200, and health covers the queues and credentials the service uses"
description: Health endpoints return non-200 status codes when dependencies fail, covering critical queues and credentials rather than just pinging an API.
example_id: E-014
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [health, availability, monitoring]
example_file: src/HealthFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on health check status codes, coverage and permissions (mined 2026-10-18)
---

# Situation

A service that relies on queues and an external partner API exposes a health check endpoint that always returns HTTP 200 with an `{"status": "unhealthy"}` payload.

# Why (verdict)

Load balancers, orchestrators, and monitoring probes evaluate the HTTP status code, not JSON response bodies. Returning 200 OK for unhealthy components fools infrastructure into routing traffic to broken instances ([OBS.1](../rules/observability/obs-1-health-reflects-reality.md)). Health checks must return failure status codes (e.g., 503) and verify essential dependencies like queues and auth tokens without requesting excessive permissions.

# Compliant pattern

## Good example

```csharp
public sealed class HealthFunctions(IPartnerService partner, IQueueProbe inbound, IQueueProbe outbound)
{
    [Function(nameof(Health))]
    public async Task<IActionResult> Health([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req,
        CancellationToken ct)
    {
        var checks = await Task.WhenAll(partner.HealthAsync(ct), inbound.HealthAsync(ct), outbound.HealthAsync(ct));
        var unhealthy = checks.Where(c => !c.IsHealthy).ToArray();

        return new ObjectResult(new { status = unhealthy.Length == 0 ? "healthy" : "unhealthy", unhealthy })
        {
            StatusCode = unhealthy.Length == 0 ? 200 : 503,
        };
    }
}
```

## Bad example

```csharp
public sealed class HealthFunctions(IPartnerService partner)
{
    [Function(nameof(Health))]
    public async Task<IActionResult> Health([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req,
        CancellationToken ct)
    {
        var result = await partner.HealthAsync(ct);          // only the API; queues are not checked
        return new OkObjectResult(new { status = result.IsHealthy ? "healthy" : "unhealthy" });   // always 200
    }
}
```

# Not verified

Written for this example in neutral names. Whether degraded (one dependency down) should return 200 is a decision per service (see the rule's boundary).

# Verification in context

[E-032](e-032-health-endpoint-fails-when-a-dependency-fails.md) shows how the dependency probe produces the health result mapped here. Use [deployment verification](../playbooks/verify-deployment.md) to inspect the deployed endpoint. [OBS.2](../rules/observability/obs-2-alerts-follow-causality.md) governs the alert consuming that result, including missing signals.
