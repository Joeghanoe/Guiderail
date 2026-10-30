---
type: Example
title: "E-034 The same catch ladder is not pasted into every endpoint"
description: Each HTTP function repeats a catch for the database exception and a catch for Exception with the same body; the mapping belongs in one place.
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

An API has a dozen endpoints. Every endpoint wraps its body in the same two catch blocks: one for the
database exception and one for `Exception`, both logging an error and returning 503. Only the log text differs
("Store error ...", "Unhandled error ..."), so the second block adds nothing the first did not already do.

# Why (verdict)

Repeated code becomes a method (CODE.4). Twelve copies drift: one endpoint forgets the not-found case, another
logs the request body, a third returns 500. One error-mapping step (middleware around the HTTP functions, or
one helper that takes the operation) decides what each exception means, logs it once with the route and the
request identifier, and the endpoints keep only the cases that are specific to them, such as a conflict on
create. The two identical catch blocks collapse into one even before that.

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
