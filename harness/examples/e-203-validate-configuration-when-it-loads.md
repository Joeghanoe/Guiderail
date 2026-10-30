---
type: Example
title: "E-203 Partner configuration is deserialised and validated once, and a bad entry fails by name"
description: A base provider reads one JSON configuration per partner, rejects an empty or unparsable entry, and asks the subclass to validate the mandatory fields; the error names the field, never the value.
example_id: E-203
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: draft
tags: [configuration, validation, errors]
example_file: src/Models/ConfigurationProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@Models/Definitions/ExternalInterfaceSettings.cs#L8-L52
  - id: evidence-subclass
    resource: b2b-ext@Services/ThirdParty/PartnerB/PartnerBConfigurationProvider.cs#L11-L32
---

# Situation

Each partner integration has its own settings stored as one JSON document per partner in a vault. An abstract base class loads
the document by partner id, deserialises it and calls an abstract `ValidateConfig()` that each partner implements.[^evidence]

# Why (verdict)

A missing document, an unparsable document and a missing mandatory field each throw `InvalidOperationException` or
`ArgumentException` with the partner id or the field name. The service never starts a call with a half-filled
configuration, so the failure shows up on the first message for that partner and names what is missing (CODE.2). The log
lines carry the partner id and the field name only, not the document, which is the right amount of detail with credentials
inside the document (SEC.2). Adding a partner is one subclass with its own validation.

Two things to improve if copying: the rethrown `InvalidOperationException` for a missing field repeats the "failed to
deserialize" message and drops the field name, and the original exception is not passed as the inner exception.

# Compliant pattern

## Good example

```csharp
public abstract class PartnerConfigurationProvider<T> where T : PartnerConfiguration
{
    public T Configuration { get; }

    protected PartnerConfigurationProvider(IConfiguration source, ILogger logger, string partnerId)
    {
        var json = source[$"{partnerId}-configuration"];
        if (string.IsNullOrEmpty(json))
        {
            throw new InvalidOperationException($"Configuration for partner {partnerId} is missing or empty");
        }

        try { Configuration = JsonConvert.DeserializeObject<T>(json)!; }
        catch (JsonException ex)
        {
            throw new InvalidOperationException($"Configuration for partner {partnerId} cannot be read", ex);
        }

        try { Validate(); }
        catch (ArgumentException ex)
        {
            throw new InvalidOperationException($"Configuration for partner {partnerId} lacks {ex.Message}", ex);
        }
    }

    protected abstract void Validate();   // throw ArgumentException(fieldName) for a missing mandatory field
}
```

## Bad example

```csharp
var json = source[$"{partnerId}-configuration"];
Configuration = JsonConvert.DeserializeObject<T>(json);   // null on empty, NullReferenceException on first use
```

# Not verified

Not run. The source constructs the provider per message (transient), so the validation repeats on each message; whether that
is wanted was not checked.

[^evidence]: Configuration provider base class of a case-sync function app.
