---
type: Example
title: "E-020 One type per file: records, interfaces, enums and validators get their own file, in C# and TypeScript"
description: Top-level types (classes, interfaces, records, enums, validators) get their own file in C# and TypeScript; only private nested helpers belong in the same file.
example_id: E-020
rule: /rules/code/code-5-one-responsibility.md
verdict: violation
status: stable
tags: [code, design, file-structure, one-type-per-file]
eval_split_files: true
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-26T00:00:00Z }
sources:
  - id: origin
    resource: direct feedback from the repo owner on a prototype app with many mixed files ("each file has a single purpose; a service can have multiple methods, but the same file shouldn't contain records etc.; future code must obey that")
---

# Situation

Code generation frequently clumps services, DTOs, interfaces, and records into single bloated files. Our convention enforces one file per top-level type, named after that type.[^origin]

# Expected verdict

The bad example violates [CODE.5](../rules/code/code-5-one-responsibility.md) by declaring `Menu` and `IMenuRepository` as sibling top-level types in `MenuService.cs`. Keep one top-level type per file. Private helpers used exclusively by one class may remain nested inside that class.

# Compliant pattern

## Good example

```csharp
// MenuService.cs
public sealed class MenuService(IMenuRepository menus)
{
    public Task<Menu?> Find(Guid id) => menus.Find(id);
}

// Menu.cs
public sealed record Menu(Guid Id, string Name);

// IMenuRepository.cs
public interface IMenuRepository
{
    Task<Menu?> Find(Guid id);
}
```

## Bad example

```csharp
// MenuService.cs
public sealed record Menu(Guid Id, string Name);

public interface IMenuRepository
{
    Task<Menu?> Find(Guid id);
}

public sealed class MenuService(IMenuRepository menus)
{
    public Task<Menu?> Find(Guid id) => menus.Find(id);
}
```

# Enforcement evidence

The Roslyn checker in tools/code implements the approved C# structural subset. Its disposable fixtures in tests/test_code_types.py cover pass, fail, inherited and error outcomes. Conditional sources require an explicit symbol configuration; evidence applies only to that configuration. TypeScript/TSX and contextual design expectations remain review responsibilities. This example does not alter reviewer thresholds.

[^origin]: repo owner feedback, 2026-10-26
