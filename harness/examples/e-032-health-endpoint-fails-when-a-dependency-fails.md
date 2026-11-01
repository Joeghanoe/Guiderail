---
type: Example
title: "E-032 A dependency probe reports failure and preserves cancellation"
description: A dependency probe performs real I/O, reports failure as Unhealthy and propagates caller cancellation instead of assuming success.
example_id: E-032
rule: /rules/observability/obs-1-health-reflects-reality.md
verdict: compliant
status: draft
tags: [health, observability, azure-functions]
example_file: src/StoreHealthCheck.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

A service depends on a document database. Its health check must establish that the dependency is reachable, report a failed probe and respect cancellation by the caller.

# Why (verdict)

A probe performs bounded, non-destructive I/O instead of assuming the dependency is healthy. A dependency failure becomes `Unhealthy`; caller cancellation propagates rather than becoming an outage report (OBS.1). [E-014](/examples/e-014-health-reports-unhealthy.md) owns dependency coverage and HTTP status mapping.

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
