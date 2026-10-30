---
type: Example
title: "E-014 Unhealthy is not a 200, and health covers the queues and credentials the service uses"
description: A health endpoint returns a failing status code when a dependency or credential is bad, and checks every dependency instead of only the API.
example_id: E-014
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [health, availability, monitoring]
example_file: src/HealthFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on health check status codes, coverage and permissions (mined 2026-10-18)
---

# Situation

A connector reads from one queue, writes to another and calls a partner API. It gets a health endpoint that
pings the partner and always answers 200 with a status in the body.

# Why (verdict)

An availability test, a load balancer and an alert rule read the status code. A 200 with `"unhealthy"` in the
body means they all see a healthy service while the credentials used for the partner have expired. The
check also ignores the queues the service cannot work without, so a broken queue is invisible. The health
call may not need more permissions than the real work (OBS.1).

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

Written for this example in neutral names. Whether degraded (one dependency down) should return 200 is a
decision per service (see the rule's boundary).
