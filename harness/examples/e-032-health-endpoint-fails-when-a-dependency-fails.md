---
type: Example
title: "E-032 A health check reports Unhealthy and the endpoint turns that into a failing status code"
description: A dependency check returns Unhealthy instead of throwing, and the health endpoint answers with a non-200 so probes and the availability timer notice.
example_id: E-032
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: compliant
status: draft
tags: [health, observability, azure-functions]
example_file: src/HealthEndpoint.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

A function app depends on a document database and an external API. Each dependency has its own health check class.
One HTTP function runs all registered checks and returns the report.

# Why (verdict)

The check answers "can this service do its work" by touching the dependency (listing containers, reading the
external API), not by returning true. A failure becomes `Unhealthy`, only cancellation is rethrown. The endpoint maps
anything other than `Healthy` to a failing status code (424 here), so the platform probe and the availability
test see an outage that a 200 with "unhealthy" in the body would hide (OBS.1).

# Compliant pattern

## Good example

```csharp
public sealed class StoreHealthCheck(StoreClient store) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct = default)
    {
        try
        {
            await store.ListContainersAsync(ct);
            return HealthCheckResult.Healthy("Store is reachable.");
        }
        catch (OperationCanceledException) when (ct.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("Store is not responding.", ex);
        }
    }
}

[Function("health")]
public async Task<HttpResponseData> Health([HttpTrigger(AuthorizationLevel.Function, "get", Route = "health")] HttpRequestData req)
{
    var report = await healthChecks.CheckHealthAsync();
    var response = req.CreateResponse(report.Status == HealthStatus.Healthy ? HttpStatusCode.OK : HttpStatusCode.FailedDependency);
    await response.WriteAsJsonAsync(new { status = report.Status.ToString() });
    return response;
}
```

## Bad example

```csharp
[Function("health")]
public async Task<HttpResponseData> Health([HttpTrigger(AuthorizationLevel.Function, "get", Route = "health")] HttpRequestData req)
{
    var report = await healthChecks.CheckHealthAsync();
    var response = req.CreateResponse(HttpStatusCode.OK);
    await response.WriteAsJsonAsync(new { status = report.Status.ToString() });
    return response;
}
```

# Not verified

Whether one slow dependency should degrade the whole report or only its own entry is a per-service decision.
