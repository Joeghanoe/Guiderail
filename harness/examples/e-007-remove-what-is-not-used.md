---
type: Example
title: "E-007 Commented-out code and unused registrations are deleted"
description: Clean up startup files by removing commented-out code, orphaned dependencies, and dead DI registrations.
example_id: E-007
rule: /rules/code/code-1-remove-what-is-not-used.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [hygiene, startup]
example_file: src/Program.cs
eval_context_files: [src/OrderHandler.cs]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on startup files, unused packages and generated scaffolding (mined 2026-10-18)
---

# Situation

After migrating hosting models, a startup file retains commented-out service registrations, unused namespaces, and resolved types that are no longer used.

# Why (verdict)

Commented-out code creates confusion about whether logic was abandoned, disabled, or temporarily parked. Version control preserves history—dead code, orphaned registrations, and unused packages should simply be deleted so maintainers do not have to decipher them (CODE.1).

# Compliant pattern

## Good example

```csharp
using Contoso.Orders;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = new HostBuilder()
    .ConfigureServices(services =>
    {
        services.AddHttpClient<IOrderClient, OrderClient>();
        services.AddHostedService<OrderWorker>();
    })
    .Build();

host.Run();
```

## Bad example

```csharp
using Contoso.Orders;
using Contoso.Orders.Legacy;                 // nothing in this file uses it
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = new HostBuilder()
    .ConfigureServices(services =>
    {
        //services.AddSingleton<IOrderClient, OrderClient>();
        services.AddHttpClient<IOrderClient, OrderClient>();
        services.AddSingleton<IReportBuilder, ReportBuilder>();   // never resolved
    })
    .Build();

host.Run();
```

# Not verified

Written for this example in neutral names. The same finding applies to a `.csproj` package reference, a setting in a config file and generated files such as `Function1.cs`; the snippet shows one of them.
