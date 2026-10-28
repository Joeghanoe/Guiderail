---
type: Case
title: "C-008 A failure is thrown or checked, not swallowed into a null"
description: A method that catches an exception and returns null makes the caller treat a failed upload as success; throw the right exception, or check the response.
case_id: C-008
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [errors, http]
example_file: src/DocumentService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on swallowed exceptions and generic exception types (mined 2026-10-18)
---

# Situation

A service uploads a file to a partner API and returns the file's identifier.

# Why (verdict)

Catching the exception and returning `null` tells the caller nothing: the action is still reported as
successful and nobody uploaded anything. A reviewer asks "when does this happen? is that on purpose?" because
the answer decides whether data is lost silently. Throwing a specific exception, or letting
`EnsureSuccessStatusCode()` throw for a failed response, keeps the failure visible where it can be handled or
reported. The logging belongs in one place, with context, once (CODE.2).

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

Written for this example in neutral names. A `Try...` method that returns a result type is a different pattern
and is allowed (see the rule's boundary).
