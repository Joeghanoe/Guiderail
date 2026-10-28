---
type: Case
title: "C-001 Services get their HttpClient injected"
description: A service receives its HttpClient through the constructor instead of creating one.
case_id: C-001
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
tags: [testability, http]
example_file: src/PartnerService.cs
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T23:00:00Z }
---

# Situation

A service calls a partner API over HTTP.

# Why (verdict)

A service that creates its own `HttpClient` cannot be tested without the real endpoint, and each instance
holds its own connection pool. Injected, the client is registered once in the composition root and replaced
by a stub handler in tests (T.2).

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
