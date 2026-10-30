---
type: Example
title: "E-010 A name used in several places is written once, and function names come from nameof"
description: Setting keys are constants shared by every reader, and a function's name is taken with nameof so a rename cannot break it.
example_id: E-010
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [duplication, configuration, dotnet]
example_file: src/OrderFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on repeated setting names, string-literal function names and duplicated blocks (mined 2026-10-18)
---

# Situation

A function app reads its queue settings in a startup extension and in a health check, and names its trigger
function with a string.

# Why (verdict)

`"ServiceBus:QueueName"` typed in two files is two chances to be different, and a typo only shows at runtime.
The trigger name typed as `"HandleMessage"` stops matching the method the moment someone renames it, and
nothing fails until the function is not found. `nameof(HandleMessage)` and a shared constant make the compiler
do the check (CODE.4).

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

Written for this example in neutral names. Attribute arguments that must be compile-time constants cannot use
`nameof` on an instance member of another type; a `const` string fits there.
