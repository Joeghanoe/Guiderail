---
type: Example
title: "E-105 When the token endpoint fails, log the status and the error code, never the body"
description: A token provider reads only the short OAuth error code from a failed response, logs it with the status code, and then lets EnsureSuccessStatusCode throw.
example_id: E-105
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: compliant
status: draft
tags: [logging, http, oauth]
example_file: src/TokenProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-04/Services/TokenProvider.cs#L137-L171
---

# Situation

A singleton token provider calls an OAuth token endpoint with a refresh token. On a failed response it must tell
a consumed refresh token (`invalid_grant`) from bad client credentials (`invalid_client`) in the logs.[^evidence]

# Why (verdict)

The error body can carry `error_description` text. The provider parses the body, keeps only the `error` field when
it is a string of at most 64 characters, falls back to `unknown` or `unparseable` (a proxy can answer with HTML),
logs the status and that code, and then calls `EnsureSuccessStatusCode()` so the failure still surfaces (CODE.2).
No token, secret or body text is logged (SEC.2). A comment says why the body is not logged, which is the
constraint the code cannot express.

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

# Not verified

The same connector logs the response body of a failed data call (a "no secrets in this body" comment justifies
it). That is a different call and is not assessed here; CODE.2 says not to log response bodies.

[^evidence]: token provider failure path
