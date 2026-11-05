---
type: Example
title: "E-035 Time comes in as a parameter or a TimeProvider, not from DateTimeOffset.UtcNow inside the service"
description: Inject TimeProvider or pass timestamps as parameters rather than reading system clocks directly, enabling deterministic time-based testing.
example_id: E-035
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:28:57Z }
tags: [testability, time]
example_file: src/RateLimiter.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
---

# Situation

A rate limiter reads `DateTimeOffset.UtcNow` directly inside its methods to evaluate sliding windows, making window expiration and delay logic untestable.

# Why (verdict)

Calling the system clock directly inside business logic makes time-dependent code (rate limits, timeouts, expirations) untestable without fragile thread sleeps (T.2). Inject .NET's `TimeProvider` or accept timestamps as parameters so unit tests can control time deterministically.

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

Extracting the clock alone does not make a method unit-testable when it also does storage I/O in the same body; the pure window logic is the part worth moving out. Durable orchestrators must keep using the orchestration context's time, not a TimeProvider.
