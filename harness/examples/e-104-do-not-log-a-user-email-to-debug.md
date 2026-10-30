---
type: Example
title: "E-104 A user's email address is written to the debug log"
description: Debug log lines interpolate the e-mail address of the person being looked up; use the object id or a count.
example_id: E-104
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: violation
status: draft
tags: [privacy, logging]
example_file: src/DirectoryClient.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-03/Services/DirectoryClient.cs#L179-L184
  - id: evidence-2
    resource: hub-conn@src/connector-03/MessageFunctions.cs#L245-L246
---

# Situation

A directory client looks a user up by e-mail address and writes `Getting user with email: {email}` at debug level.
Elsewhere in the same connector, warnings carry the user principal name and the manager's e-mail address.[^evidence]

# Why (verdict)

An e-mail address and a user principal name identify a person. SEC.2 forbids personal data in logs and telemetry at
any level; debug is switched on in production when an incident needs it. Log the operation and an identifier that
is not personal (the directory object id, the message id), or a count. The lookup keeps working the same way.

# Compliant pattern

## Good example

```csharp
public async Task<User> GetUserAsync(string email, ILogger log)
{
    log.LogDebug("Looking up a user by e-mail address");
    var user = await graph.Users[email].GetAsync();
    log.LogDebug("Found user {UserId}", user?.Id);
    return user;
}
```

## Bad example

```csharp
public async Task<User> GetUser(ILogger log, string email)
{
    log.LogDebug($"Getting user with email: {email} from the directory.");
    return await graph.Users[email].GetAsync();
}
```

# Not verified

Whether the directory object id counts as personal data under the customer's policy was not checked; the rule
treats identifiers as acceptable (see E-002).

[^evidence]: debug and warning lines that interpolate an e-mail address or principal name
