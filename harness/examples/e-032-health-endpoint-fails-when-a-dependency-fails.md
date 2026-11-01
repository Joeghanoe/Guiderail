---
type: Example
title: "E-032 A dependency probe reports failure and preserves cancellation"
description: Dependency health probes execute bounded I/O, report reachability failures as Unhealthy, and propagate cancellation tokens cleanly.
example_id: E-032
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: compliant
status: draft
tags: [health, observability, azure-functions]
example_file: src/StoreHealthCheck.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

A service needs to verify document database connectivity in its health check while honoring cancellation tokens.

# Why (verdict)

Probing a dependency requires bounded, lightweight I/O rather than assuming health. When dependencies fail, report `Unhealthy`; when the caller cancels the check, propagate the cancellation rather than falsely alerting an outage (OBS.1). [E-014](/examples/e-014-health-reports-unhealthy.md) covers full HTTP status mapping.

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
```

## Bad example

```csharp
public sealed class StoreHealthCheck(StoreClient store) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct = default)
    {
        try
        {
            await store.ListContainersAsync(ct);
        }
        catch (Exception)
        {
            // Dependency failures and caller cancellation both disappear.
        }

        return HealthCheckResult.Healthy("Store is reachable.");
    }
}
```

# Not verified

The SDK's probe timeout and required permissions must be checked in the implementing service. Endpoint status mapping is evaluated separately by E-014.
