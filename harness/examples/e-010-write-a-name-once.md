---
type: Example
title: "E-010 A name used in several places is written once, and function names come from nameof"
description: Share configuration keys as constants across readers, and use nameof for function trigger names so renames fail at compile time.
example_id: E-010
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [duplication, configuration, dotnet]
example_file: src/OrderFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on repeated setting names, string-literal function names and duplicated blocks (mined 2026-10-18)
---

# Situation

A function app reads queue settings across multiple files using string literals and binds trigger names with hardcoded strings.

# Why (verdict)

Hardcoding string keys like `"ServiceBus:QueueName"` in multiple places invites typos that only surface at runtime. Hardcoding trigger names also breaks silently when methods are renamed. Use shared constants for configuration keys and `nameof()` for trigger names so the compiler enforces correctness (CODE.4).

# Compliant pattern

## Good example

```csharp
public static class SettingNames
{
    public const string QueueName = "ServiceBus:QueueName";
    public const string Namespace = "ServiceBus:FullyQualifiedNamespace";
}

public sealed class OrderFunctions
{
    [Function(nameof(HandleMessage))]
    public Task HandleMessage([ServiceBusTrigger("%" + SettingNames.QueueName + "%")] string message) =>
        Task.CompletedTask;
}

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddQueue(this IServiceCollection services, IConfiguration config) =>
        services.AddSingleton(new QueueSettings(config[SettingNames.Namespace]!, config[SettingNames.QueueName]!));
}
```

## Bad example

```csharp
public sealed class OrderFunctions
{
    [Function("HandleMessage")]
    public Task HandleMessage([ServiceBusTrigger("%ServiceBus:QueueName%")] string message) =>
        Task.CompletedTask;
}

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddQueue(this IServiceCollection services, IConfiguration config) =>
        services.AddSingleton(new QueueSettings(config["ServiceBus:FullyQualifiedNamespace"]!, config["ServiceBus:QueueName"]!));
}

public sealed class OrderHealthCheck(IConfiguration config)
{
    public string Queue => config["ServiceBus:QueueName"]!;        // the same key a third time
}
```

# Not verified

Written for this example in neutral names. Attribute arguments that must be compile-time constants cannot use `nameof` on an instance member of another type; a `const` string fits there.
