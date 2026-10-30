---
type: Example
title: "C-NNN Every error code in the catalog has a row in the runbook, and a test fails when one is missing"
description: An error-code catalog in code and its operations page are two sides of one list; a test reads the page and names each code that has no row.
example_id: C-NNN
rule: /rules/code/code-7-linked-changes.md
verdict: compliant
status: draft
tags: [code, docs, runbook, error-codes, tests]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-24T12:00:00Z }
---

# Situation

A worker classifies every failure into a numbered code with an owner and one action. Support reads the
codes on an operations page, `docs/operations/error-codes.md`, and customers quote them in tickets. The
catalog lives in code; the page is Markdown. A new code added to the catalog without a row leaves support
with a number nobody can look up.

# Why (compliant)

The catalog and the page share one list across two file kinds, so CODE.4 cannot make it one name. CODE.7
asks for the next best thing: a test that reads both sides at build time. A missing row fails the build
with the code in the message, not the first alert mail that quotes it.

# Compliant pattern

The test walks up to the repo root, reads the page and asserts that every catalog code appears in it.

## Good example

```csharp
public class ErrorCatalogTests
{
    [Test]
    public void Every_code_has_a_row_on_the_operations_page()
    {
        var page = File.ReadAllText(Path.Combine(RepositoryRoot(), "docs", "operations", "error-codes.md"));

        var missing = ErrorCatalog.All
            .Select(e => $"`ERR-{e.Number}`")
            .Where(code => !page.Contains(code, StringComparison.Ordinal))
            .ToList();

        Assert.That(missing, Is.Empty, "codes missing from docs/operations/error-codes.md");
    }

    private static string RepositoryRoot()
    {
        for (var dir = new DirectoryInfo(TestContext.CurrentContext.TestDirectory); dir is not null; dir = dir.Parent)
        {
            if (Directory.Exists(Path.Combine(dir.FullName, "docs", "operations")))
            {
                return dir.FullName;
            }
        }

        throw new DirectoryNotFoundException("docs/operations not found above the test directory");
    }
}
```

## Bad example

```csharp
/// <summary>
/// Error codes. Keep docs/operations/error-codes.md in sync when you add one.
/// </summary>
public static class ErrorCatalog
{
    public static readonly ErrorCode[] All =
    [
        new(1101, "DB-FIREWALL", Owner.Customer, "Add the egress IP to the database firewall."),
        new(1102, "DB-LOGIN", Owner.Customer, "Create the database user for the readers group."),
        new(2201, "STORAGE-ACCESS", Owner.Us, "Check the worker's role on the bucket."),
    ];
}
```

# Not verified

Whether the eval reviewer flags a comment-only "keep in sync" as CODE.7 without seeing the docs page in the
same diff.
