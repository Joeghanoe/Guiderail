---
type: Example
title: "E-008 A failure is thrown or checked, not swallowed into a null"
description: Surface HTTP and upload errors with explicit exceptions or EnsureSuccessStatusCode rather than swallowing them into nulls.
example_id: E-008
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [errors, http]
example_file: src/DocumentService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on swallowed exceptions and generic exception types (mined 2026-10-18)
---

# Situation

A service uploads documents to a partner API, catching all exceptions and returning null on failure.

# Why (verdict)

Catching exceptions and returning `null` masks catastrophic failures—callers mistakenly treat nulls as successful operations, silently dropping files (CODE.2). Allow `EnsureSuccessStatusCode()` or custom exceptions to bubble up so errors are logged with context and handled appropriately.

# Compliant pattern

## Good example

```csharp
public sealed class DocumentService(HttpClient http, ILogger<DocumentService> logger)
{
    public async Task<string> UploadAsync(string name, Stream content, CancellationToken ct)
    {
        using var response = await http.PostAsync($"documents/{name}", new StreamContent(content), ct);
        response.EnsureSuccessStatusCode();

        var id = await response.Content.ReadAsStringAsync(ct);
        if (string.IsNullOrEmpty(id))
        {
            throw new InvalidDataException($"Upload of {name} returned no document id.");
        }

        logger.LogInformation("Uploaded document {DocumentId}", id);
        return id;
    }
}
```

## Bad example

```csharp
public sealed class DocumentService(HttpClient http, ILogger<DocumentService> logger)
{
    public async Task<string?> UploadAsync(string name, Stream content, CancellationToken ct)
    {
        try
        {
            using var response = await http.PostAsync($"documents/{name}", new StreamContent(content), ct);
            if (!response.IsSuccessStatusCode)
            {
                throw new InvalidOperationException("Upload failed");
            }

            return await response.Content.ReadAsStringAsync(ct);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Upload failed");
            logger.LogError("Name was {Name}", name);
            return null;
        }
    }
}
```

# Not verified

Written for this example in neutral names. A `Try...` method that returns a result type is a different pattern and is allowed (see the rule's boundary).
