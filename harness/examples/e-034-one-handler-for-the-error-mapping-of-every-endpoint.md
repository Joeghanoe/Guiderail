---
type: Example
title: "E-034 The same catch ladder is not pasted into every endpoint"
description: Centralize endpoint exception handling in middleware or shared helpers rather than duplicating identical catch blocks across every route.
example_id: E-034
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: draft
tags: [duplication, http, errors]
example_file: src/OrdersFunction.cs
eval_context_files: [src/CustomersFunction.cs]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

Multiple API endpoints repeat the same catch blocks for database exceptions and general errors, logging nearly identical messages and returning HTTP 503.

# Why (verdict)

Copy-pasting catch blocks across endpoints leads to inconsistency and drift (CODE.4). Centralize exception translation in middleware or a shared error handler to ensure uniform status codes, structured logging, and correlation tracking across all routes.

# Compliant pattern

## Good example

```csharp
// Registered once for every HTTP function.
public sealed class ErrorMappingMiddleware(ILogger<ErrorMappingMiddleware> logger) : IFunctionsWorkerMiddleware
{
    public async Task Invoke(FunctionContext context, FunctionExecutionDelegate next)
    {
        try
        {
            await next(context);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled error in {Function}", context.FunctionDefinition.Name);
            var request = await context.GetHttpRequestDataAsync();
            context.GetInvocationResult().Value = await request!.ServiceUnavailableAsync();
        }
    }
}
```

## Bad example

```csharp
try
{
    var items = await service.GetAllAsync(ct);
    return await request.OkAsync(items);
}
catch (StoreException ex)
{
    logger.LogError(ex, "Store error fetching items");
    return await request.ServiceUnavailableAsync();
}
catch (Exception ex)
{
    logger.LogError(ex, "Unhandled error fetching items");
    return await request.ServiceUnavailableAsync();
}
```

# Not verified

A conflict or not-found catch inside an endpoint is specific and stays.
