---
type: Example
title: "E-200 An API client that catches everything and returns default hides the failure"
description: A gateway client logs a failed call and returns default, so every caller gets a null it has to remember to check; throw instead and let the one place that knows the policy decide.
example_id: E-200
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, http, null]
example_file: src/Services/GatewayClient.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@Services/ApiClients/ApimClient.cs#L20-L49
---

# Situation

A function app reads case data from a ticketing system through an API gateway. One generic client method sends the request,
checks the status code and deserialises the body. Around all of it sits a `catch (Exception)` that logs and returns `default`.[^evidence]

# Why (verdict)

The method throws for a non-success status and then immediately catches its own exception, so a 500, a timeout and a
malformed body all end as `null`. Each caller now has to guess whether `null` means "not found" or "the call failed".
Some callers check it, some dereference it, and a failed worknote update is reported as done (CODE.2). The status check
already did the right thing; the catch undoes it. Let the exception leave. The entry point of the message handler is the
one place that decides whether a failure is retried, dead-lettered or only warned about.

# Compliant pattern

## Good example

```csharp
public sealed class GatewayClient(HttpClient http) : IGatewayClient
{
    public async Task<T> SendAsync<T>(HttpMethod method, string path, string? json, CancellationToken ct)
    {
        using var request = new HttpRequestMessage(method, path);
        if (!string.IsNullOrEmpty(json))
        {
            request.Content = new StringContent(json, Encoding.UTF8, "application/json");
        }

        using var response = await http.SendAsync(request, ct);
        response.EnsureSuccessStatusCode();

        var body = await response.Content.ReadAsStringAsync(ct);
        return JsonConvert.DeserializeObject<T>(body)
            ?? throw new InvalidDataException($"{method} {path} returned an empty body.");
    }
}
```

## Bad example

```csharp
public async Task<T> SendAsync<T>(HttpMethod method, string path, string payload)
{
    try
    {
        var response = await _http.SendAsync(new HttpRequestMessage(method, path) { Content = Body(payload) });
        if (!response.IsSuccessStatusCode)
        {
            throw new Exception($"{method} {path} failed with {response.StatusCode}");
        }

        return JsonConvert.DeserializeObject<T>(await response.Content.ReadAsStringAsync());
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Call to {Path} failed", path);
        return default;
    }
}
```

# Not verified

Not run. The source has no tests; the callers' null handling was read, not traced for every call site.

[^evidence]: Gateway client of a case-sync function app.
