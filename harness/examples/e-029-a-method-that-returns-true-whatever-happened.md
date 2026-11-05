---
type: Example
title: "E-029 A wrapper returns true or default after a failed call, so the handler reports success"
description: A helper swallows exceptions and returns a default value, causing public methods to report success even when downstream API calls fail.
example_id: E-029
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:28:57Z }
tags: [errors, http, queue]
example_file: src/Services/InternalApiClient.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

A queue-triggered function forwards events to an internal API using a private helper that catches all exceptions, logs them, and returns `default`. Callers assume the call worked—for example, `SubmitUpdate` always returns `true`—masking failed requests as successful runs.

# Why (verdict)

Queue messages complete whenever a handler exits without throwing. Swallowing failures acknowledges the message, losing the update without retries or dead-lettering ([CODE.2](../rules/code/code-2-fail-loudly.md)). Let errors throw or call `EnsureSuccessStatusCode()`, and only return a value when it provides meaningful status to the caller.

# Compliant pattern

## Good example

```csharp
public async Task SubmitUpdateAsync(Authorization auth, Update update, CancellationToken ct)
{
    using var request = Build(HttpMethod.Post, "updates/v1", auth, update);
    using var response = await http.SendAsync(request, ct);
    response.EnsureSuccessStatusCode();   // a rejected comment fails the message; the bus retries or dead-letters it
}
```

## Bad example

```csharp
public async Task<bool> SubmitUpdate(Authorization auth, Update update)
{
    await Call<UpdateResponse>(HttpMethod.Post, "updates/v1", auth, Serialize(update));  // Call() catches and returns default
    return true;
}
```
