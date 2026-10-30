---
type: Example
title: "E-301 A failed vendor response is thrown, not turned into an empty result that advances the checkpoint"
description: A paged reader returns null on a non-success status, the caller treats null as no rows, and an incremental load saves its checkpoint over a gap.
example_id: E-301
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, http, ingestion]
example_file: src/VendorReader.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-back@ingest/Services/VendorService.cs#L241-L255
  - id: evidence-2
    resource: aq-back@ingest/Services/VendorService.cs#L129-L130
  - id: evidence-3
    resource: aq-back@ingest/Services/VendorService.cs#L350-L355
---

# Situation

An incremental ingest reads a vendor API page by page, writes the rows to storage, then saves "last successful
load" so the next run starts from there. The low-level GET method logs a warning for a non-success status and
returns `null`. The paging method passes that `null` to a helper that maps `null` to an empty list, so a page
that failed looks like the last page.

# Why (verdict)

A 401 after a key rotation, a 500 or a 403 on one endpoint all end the loop as "no more rows". The run reports
success, writes fewer rows than exist, and saves the checkpoint, so the next run starts after the gap and the
missing rows are never loaded. The only trace is a warning line. Throwing for every status the caller did not
expect (or calling `EnsureSuccessStatusCode()`) stops the run before the checkpoint moves. A status that is
known to be normal, such as a 404 for an optional sub-resource, is handled by name where it is expected and
returns an explicit "not present" result (CODE.2).

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

I did not run the ingest. The 429 branch in the same method retries and is a different, correct pattern.
Whether the caller should retry a transient 5xx before failing is a design choice this example does not make.
