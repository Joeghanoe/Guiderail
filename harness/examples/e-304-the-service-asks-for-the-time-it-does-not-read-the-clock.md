---
type: Example
title: "E-304 Time comes in as a parameter or a TimeProvider, not from DateTimeOffset.UtcNow inside the service"
description: A rate limiter that reads the clock itself cannot be tested for its window logic; a builder that receives the snapshot time as an argument can.
example_id: E-304
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: draft
tags: [testability, time]
example_file: src/RateLimiter.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-back@ingest/Services/TableStorageRateLimitService.cs#L48-L63
  - id: evidence-2
    resource: aq-back@ruleengine/Services/HealthSnapshotBuilder.cs#L26-L30
---

# Situation

Two services in the same solution treat time differently. The snapshot builder takes the snapshot time as a
parameter, and its tests pass fixed instants. The rate limiter reads `DateTimeOffset.UtcNow` in three places to
find the current minute window, decide whether it is blocked, and compute how long to wait.

# Why (verdict)

The limiter's behaviour is entirely about time: the window rolls over at minute boundaries, a block expires,
a wait is computed. With the clock read inside, a test can only run in real time or skip those paths. Taking a
`TimeProvider` (built in since .NET 8) through the constructor lets a test set the minute and assert the wait
without sleeping (T.2). The composition root registers `TimeProvider.System`.

# Compliant pattern

## Good example

```csharp
public sealed class RateLimiter(TimeProvider clock, IOptions<RateLimitOptions> options)
{
    public TimeSpan WaitFor(RateLimitState state)
    {
        var now = clock.GetUtcNow();
        var windowStart = new DateTimeOffset(now.Year, now.Month, now.Day, now.Hour, now.Minute, 0, TimeSpan.Zero);

        if (state.BlockedUntil > now)
        {
            return state.BlockedUntil - now;
        }

        return state.WindowStart == windowStart && state.Count >= options.Value.MaxPerMinute
            ? windowStart.AddMinutes(1) - now
            : TimeSpan.Zero;
    }
}
```

## Bad example

```csharp
public sealed class RateLimiter(IOptions<RateLimitOptions> options)
{
    public TimeSpan WaitFor(RateLimitState state)
    {
        var now = DateTimeOffset.UtcNow;
        var windowStart = new DateTimeOffset(now.Year, now.Month, now.Day, now.Hour, now.Minute, 0, TimeSpan.Zero);

        if (state.BlockedUntil > now)
        {
            return state.BlockedUntil - now;
        }

        return state.WindowStart == windowStart && state.Count >= options.Value.MaxPerMinute
            ? windowStart.AddMinutes(1) - now
            : TimeSpan.Zero;
    }
}
```

# Not verified

In the source the limiter also does the storage read and write in the same method, so extracting the clock
alone does not make the whole method unit-testable; the pure window logic is the part worth moving out.
Durable orchestrators must keep using the orchestration context's time, not a TimeProvider.
