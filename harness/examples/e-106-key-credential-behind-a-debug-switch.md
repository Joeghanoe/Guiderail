---
type: Example
title: "E-106 A shared key is used in a DEBUG build; release uses the managed identity"
description: The composition root chooses between an access key and the managed identity with a compiler switch, and reads a hand-built list of per-tenant secrets by string name.
example_id: E-106
rule: /rules/security/sec-3-identity-without-secrets.md
verdict: violation
status: draft
tags: [identity, configuration, dotnet]
example_file: src/Program.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-02/Program.cs#L36-L80
---

# Situation

A connector's `Program.cs` registers an event publisher. Under `#if DEBUG` it builds the client from an endpoint and
an access key read from configuration; otherwise it uses `DefaultAzureCredential`. The same file reads
`ServiceBus:QueueName`, `KeyVaultName` and `Vendor:AllowedCompanies` as raw strings in two places, and builds
per-company secret names by concatenation.[^evidence]

# Why (verdict)

Two authentication paths means the debug path is the one that is never exercised in the environment, and an
`Events-Key` secret has to exist for local work (SEC.3). `DefaultAzureCredential` already falls back to the
developer's own login locally, so the switch is not needed. The repeated string keys are a CODE.4 problem: a typed
options class bound once replaces them. Another connector in the same repo registers its clients through a shared
composition helper and one options class, which is the shape to copy (CODE.8).

# Compliant pattern

## Good example

```csharp
services.AddSingleton(sp =>
{
    var options = sp.GetRequiredService<IOptions<EventPublisherOptions>>().Value;
    return new EventGridPublisherClient(options.Endpoint, new DefaultAzureCredential());
});

services.AddOptions<EventPublisherOptions>()
    .BindConfiguration(EventPublisherOptions.SectionName)
    .ValidateOnStart();
```

## Bad example

```csharp
services.AddSingleton<EventGridPublisherClient>(sp =>
{
    var config = sp.GetRequiredService<IConfiguration>();
    string endpoint = config.GetValue<string>("Events:Endpoint");
#if DEBUG
    string key = config.GetValue<string>("Events-Key");
    return new EventGridPublisherClient(new Uri(endpoint), new AzureKeyCredential(key));
#else
    return new EventGridPublisherClient(new Uri(endpoint), new DefaultAzureCredential());
#endif
});
```

# Not verified

Whether the publisher topic has local authentication disabled was not checked (that is infrastructure, in another
component). Whether a developer's login has publish rights locally was not checked.

[^evidence]: composition root with a DEBUG-only key credential
