---
type: Example
title: "E-033 A failed external API response is thrown, not turned into an empty result that advances the checkpoint"
description: A paginated API reader returns null on non-success statuses, tricking callers into treating errors as the end of data and advancing checkpoints past missing rows.
example_id: E-033
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:28:57Z }
tags: [errors, http, ingestion]
example_file: src/ExternalApiReader.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

An incremental ingest job fetches paginated data and saves a checkpoint timestamp on completion. When a page request returns an error (401, 403, 500), the reader logs a warning and returns `null`, which the pagination helper interprets as an empty list (end of pages).

# Why (verdict)

Treating HTTP errors as empty pages causes ingestion jobs to report success and advance checkpoints over missing data (CODE.2). Unexpected status codes must throw or call `EnsureSuccessStatusCode()` to abort the checkpoint. Only explicitly expected responses (like 404 on an optional sub-resource) should be handled as empty results.

# Compliant pattern

## Good example

```csharp
private async Task<JsonNode?> GetAsync(string path, CancellationToken ct)
{
    using var response = await http.GetAsync(path, ct);

    if (response.StatusCode == HttpStatusCode.NotFound && optionalPaths.Contains(path))
    {
        return null; // documented: this sub-resource does not exist for every record
    }

    response.EnsureSuccessStatusCode();
    return await response.Content.ReadFromJsonAsync<JsonNode>(ct);
}
```

## Bad example

```csharp
private async Task<JsonNode?> GetAsync(string path, CancellationToken ct)
{
    using var response = await http.GetAsync(path, ct);

    if (!response.IsSuccessStatusCode)
    {
        logger.LogWarning("Request to {Path} failed with status {Status}", path, response.StatusCode);
        return null;
    }

    return await response.Content.ReadFromJsonAsync<JsonNode>(ct);
}

private static JsonArray ExtractRows(JsonNode? payload) => payload is null ? [] : ReadRows(payload);
```

# Not verified

The retry of a throttled response (429) is a different, correct pattern. Whether the caller should retry a transient 5xx before failing is a design choice this example does not make.
