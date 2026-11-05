---
type: Example
title: "E-001 Services get their HttpClient injected"
description: A service receives HttpClient via dependency injection instead of instantiating its own.
example_id: E-001
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-18T18:52:51Z }
tags: [testability, http]
example_file: src/PartnerService.cs
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T23:00:00Z }
---

# Situation

A service sends requests to an external partner API.

# Why (verdict)

Instantiating `HttpClient` directly leads to socket exhaustion under load and prevents unit tests from mocking network calls. Injecting `HttpClient` centralizes connection pool management and lets tests inject a mock handler (T.2).

# Compliant pattern

## Good example

```csharp
public sealed class PartnerService(HttpClient http)
{
    public Task<string> GetStatusAsync(string caseId, CancellationToken ct) =>
        http.GetStringAsync($"cases/{caseId}/status", ct);
}
```

## Bad example

```csharp
public sealed class PartnerService
{
    public Task<string> GetStatusAsync(string caseId, CancellationToken ct)
    {
        var http = new HttpClient { BaseAddress = new Uri("https://partner.example.com/") };
        return http.GetStringAsync($"cases/{caseId}/status", ct);
    }
}
```

# Not verified

Written for this example in neutral names; not taken from one project.
