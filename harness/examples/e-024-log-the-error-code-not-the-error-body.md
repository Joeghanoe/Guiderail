---
type: Example
title: "E-024 When the token endpoint fails, log the status and the error code, never the body"
description: A token provider logs the HTTP status and short OAuth error code from a failed response, never the full response body.
example_id: E-024
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: compliant
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:28:57Z }
tags: [logging, http, oauth]
example_file: src/TokenProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
---

# Situation

An OAuth token provider needs to distinguish between an expired refresh token (`invalid_grant`) and bad client credentials (`invalid_client`) in operational logs.

# Why (verdict)

Error response bodies can leak sensitive tokens, descriptions, or proxy HTML into log stores (SEC.2). Extract only the standard error code (e.g., `invalid_grant`), log it alongside the status code, and throw via `EnsureSuccessStatusCode()` so the failure surfaces cleanly without exposing payloads (CODE.2).

# Compliant pattern

## Good example

```csharp
using var response = await client.SendAsync(request, ct);
if (!response.IsSuccessStatusCode)
{
    // The error code tells a consumed token from bad credentials. The body can hold
    // error_description and is never logged.
    logger.LogWarning("Token endpoint failed with {StatusCode} {OAuthError}",
        (int)response.StatusCode, await ReadErrorCodeAsync(response, ct));
    response.EnsureSuccessStatusCode();
}

private static async Task<string> ReadErrorCodeAsync(HttpResponseMessage response, CancellationToken ct)
{
    try
    {
        using var body = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync(ct), cancellationToken: ct);

        if (!body.RootElement.TryGetProperty("error", out var error) || error.ValueKind != JsonValueKind.String)
            return "unknown";

        var code = error.GetString()!;
        return code.Length <= 64 ? code : "unknown";   // a short code, never free text
    }
    catch (JsonException)
    {
        return "unparseable";                          // a proxy can answer with HTML
    }
}
```

## Bad example

```csharp
if (!response.IsSuccessStatusCode)
{
    var body = await response.Content.ReadAsStringAsync(ct);
    logger.LogWarning("Token endpoint failed: {Body}", body);
}
```
