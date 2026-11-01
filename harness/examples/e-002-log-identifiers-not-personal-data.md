---
type: Example
title: "E-002 Log identifiers, not personal data"
description: Log statements include support lookup IDs instead of personally identifiable information like names or email addresses.
example_id: E-002
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-20T19:47:15Z }
tags: [privacy, logging]
example_file: src/NotificationService.cs
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T23:00:00Z }
---

# Situation

A service logs customer notification events.

# Why (verdict)

Writing personal details (names, emails) into log lines leaks PII into downstream logging platforms, support tickets, and external exports (SEC.2). Log a customer or entity ID instead, giving support teams the necessary lookup reference without exposing personal data.

# Compliant pattern

## Good example

```csharp
public sealed class NotificationService(IMailSender mail, ILogger<NotificationService> logger)
{
    public async Task NotifyAsync(Customer customer, CancellationToken ct)
    {
        await mail.SendAsync(customer.Email, "Your example was updated", ct);
        logger.LogInformation("Notification sent for customer {CustomerId}", customer.Id);
    }
}
```

## Bad example

```csharp
public sealed class NotificationService(IMailSender mail, ILogger<NotificationService> logger)
{
    public async Task NotifyAsync(Customer customer, CancellationToken ct)
    {
        await mail.SendAsync(customer.Email, "Your example was updated", ct);
        logger.LogInformation("Notification sent to {Email} ({Name})", customer.Email, customer.FullName);
    }
}
```

# Variant: request and response bodies

The same rule covers whole payloads. A body is personal data and sometimes a secret in one piece, and the fields in it change without anyone touching the logging line. Log the identifier, the status and the size.

```csharp
// Bad: the complete response body, which may contain personal data or secrets, ends up in the log store.
logger.LogInformation("Partner call {Url} returned {Body}", url, await response.Content.ReadAsStringAsync(ct));

// Good: enough to find the call again, nothing that identifies a person or exposes the payload.
logger.LogInformation("Partner call {Operation} returned {StatusCode} ({Length} bytes)",
    operation, (int)response.StatusCode, response.Content.Headers.ContentLength);
```

When a failure needs the body to be understood, log the part the partner documents as safe (an error code or a correlation id), not the whole body.

# Not verified

Written for this example in neutral names; not taken from one project. Variant added from recurring review feedback on logged request and response bodies; needs a human pass.
