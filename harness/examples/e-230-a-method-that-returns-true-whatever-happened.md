---
type: Example
title: "E-230 A wrapper returns true or default after a failed call, so the handler reports success"
description: A private call helper swallows every exception and returns default; public methods then return true or dereference the null, so a failed partner call looks like a processed message.
example_id: E-230
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, http, queue]
example_file: src/Services/CustomerApiService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-hook@Services/ApiClients/CustomerApiService.cs#L54-L112
---

# Situation

A queue-triggered function receives a partner's webhook and forwards it to an internal API. The API service has one private
`Call<T>` helper. A `try/catch (Exception)` around it logs and returns `default`. Public methods build on that: `CreateComment`
awaits the call and then returns `true`; `ChangeStatus` returns whatever `default(bool)` gives, which is `false` for a failure
and also for a legitimate "no change".[^evidence]

# Why (verdict)

The queue message is completed when the function returns without throwing. With the failure swallowed in the helper, a
comment that the internal API rejected is acknowledged, never retried and never reaches the dead-letter queue, and the
operator sees a successful run (CODE.2). A method called `CreateComment` returning `true` unconditionally tells the caller
nothing. Let the helper throw (or call `EnsureSuccessStatusCode`), and keep a return value only where the answer is
information (found or not found).

# Compliant pattern

## Good example

```csharp
public async Task CreateCommentAsync(Authorization auth, CaseComment comment, CancellationToken ct)
{
    using var request = Build(HttpMethod.Post, "comments/v1", auth, comment);
    using var response = await http.SendAsync(request, ct);
    response.EnsureSuccessStatusCode();   // a rejected comment fails the message; the bus retries or dead-letters it
}
```

## Bad example

```csharp
public async Task<bool> CreateComment(Authorization auth, CaseComment comment)
{
    await Call<CommentResponse>(HttpMethod.Post, "comments/v1", auth, Serialize(comment));  // Call() catches and returns default
    return true;
}
```

# Not verified

Not run. The source's retry and dead-letter settings were not checked, so what the bus does after the throw is assumed.

[^evidence]: API service of a webhook-to-case function app.
