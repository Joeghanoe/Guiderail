---
type: Example
title: "E-011 A health endpoint is its own class, and the client decides what its response means"
description: The health function does not share a class with business functions, and the service class answers "is it healthy" itself instead of passing the raw response out.
example_id: E-011
rule: /rules/code/code-5-one-responsibility.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [design, health]
example_file: src/PartnerService.cs
eval_context_files: [src/HealthFunctions.cs]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on class and file layout, responsibility of the service class and separated deployment files (mined 2026-10-18)
---

# Situation

A connector has business functions and now gets a health endpoint. The change puts the health function in the
same class as the business functions and has the service return the partner's raw ping response for the
function to interpret.

# Why (verdict)

The health function has nothing to do with the partner functionality, so the class now has two reasons to
change. The service class is the one that knows the partner; when it hands out the raw response, the decision
"is the partner healthy" moves to the caller, which will not agree with the next caller. One class per job,
and the class that talks to a dependency decides what its answer means (CODE.5).

# Compliant pattern

## Good example

```csharp
public sealed class PartnerService(HttpClient http) : IPartnerService
{
    public async Task<HealthResult> HealthAsync(CancellationToken ct)
    {
        using var response = await http.GetAsync("ping", ct);
        return response.IsSuccessStatusCode ? HealthResult.Healthy : HealthResult.Unhealthy("ping failed");
    }
}
```

The `HealthFunctions` entry point lives separately in `src/HealthFunctions.cs`.

## Bad example

```csharp
public sealed class PartnerService(HttpClient http) : IPartnerService
{
    public Task<HttpResponseMessage> PingAsync(CancellationToken ct) => http.GetAsync("ping", ct);
}

public sealed class PartnerFunctions(IPartnerService partner)
{
    [Function(nameof(CreateContact))]
    public Task CreateContact(/* ... */) => Task.CompletedTask;

    [Function(nameof(Health))]               // unrelated to creating contacts
    public async Task<IActionResult> Health([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req,
        CancellationToken ct)
    {
        var response = await partner.PingAsync(ct);     // the function decides what the response means
        return new OkObjectResult(response.StatusCode);
    }
}
```

# Not verified

Written for this example in neutral names. The status-code part of the good example is the subject of E-014.
