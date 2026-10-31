---
type: Example
title: "E-022 A health endpoint returns a failing status when a dependency is down"
description: The service's health function maps an unhealthy result to 424 and lists each dependency, so probes and availability tests notice.
example_id: E-022
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: compliant
status: draft
tags: [health, observability, dotnet]
example_file: src/HealthCheckFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
---

# Situation

A function app exposes `GET api/health`. The health service aggregates one check per dependency (the external API,
the event publisher, the queue).

# Why (verdict)

The endpoint returns 200 only when every check is healthy and 424 (Failed Dependency) otherwise, and the body lists
each check with its status. An availability test that only reads the status code therefore fails when a dependency
fails (OBS.1). The endpoint is its own class, apart from the business functions (CODE.5).

# Compliant pattern

## Good example

```csharp
public sealed class HealthFunctions(HealthCheckService health)
{
    [Function(nameof(Health))]
    public async Task<HttpResponseData> Health(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "api/health")] HttpRequestData req)
    {
        var result = await health.CheckHealthAsync();

        var status = result.Status == HealthStatus.Healthy
            ? HttpStatusCode.OK
            : HttpStatusCode.FailedDependency;

        var response = req.CreateResponse(status);
        await response.WriteAsJsonAsync(new
        {
            status = result.Status.ToString(),
            results = result.Entries.ToDictionary(e => e.Key, e => e.Value.Status.ToString())
        });
        return response;
    }
}
```

## Bad example

```csharp
public async Task<HttpResponseData> Health(HttpRequestData req)
{
    var result = await health.CheckHealthAsync();
    var response = req.CreateResponse(HttpStatusCode.OK);   // unhealthy is still 200
    await response.WriteStringAsync(result.Status.ToString());
    return response;
}
```
