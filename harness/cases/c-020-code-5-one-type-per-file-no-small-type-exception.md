---
type: Case
title: "C-020 One type per file: records, interfaces, enums and validators get their own file, in C# and TypeScript"
description: Separate top-level types into their own files; only private nested helpers qualify for the approved exception.
case_id: C-020
rule: /rules/code/code-5-one-responsibility.md
verdict: violation
status: stable
tags: [code, design, file-structure, one-type-per-file]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-26T00:00:00Z }
sources:
  - id: origin
    resource: direct feedback from the repo owner on a prototype app with many mixed files ("each file has a single purpose; a service can have multiple methods, but the same file shouldn't contain records etc.; future code must obey that")
---

# Situation

Generated code drifts into files that hold a service plus the records, DTOs, interfaces or enums it uses, and
React files that hold a component plus its types and helpers. The repo owner's convention, shared by the
company, is one file per class, interface, record, enum, service or validator, named after it.[^origin]

# Expected verdict

The bad example violates the approved CODE.5 convention: Menu and IMenuRepository are sibling
top-level types in MenuService.cs. The good example complies. Report the violation as minor.

The approved rule covers C#, TypeScript and TSX. Private helpers nested inside their only user may
remain in that user's file; small sibling types may not. On a touched mixed file, split out only types
added or changed. Generated C# files are excluded; partial declarations may use Type.cs or Type.Part.cs.
These scope decisions were accepted on 2026-10-29 in docs/evaluation/engineering-standards-decisions.md.

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

The Roslyn checker in tools/code implements the approved C# structural subset. Its disposable fixtures
in tests/test_code_types.py cover pass, fail, inherited and error outcomes. Conditional sources require
an explicit symbol configuration; evidence applies only to that configuration. TypeScript/TSX and
contextual design expectations remain review responsibilities. This case does not alter reviewer thresholds.

[^origin]: repo owner feedback, 2026-10-26
