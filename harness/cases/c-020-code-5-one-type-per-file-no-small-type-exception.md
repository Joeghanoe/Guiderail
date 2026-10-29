---
type: Case
title: "C-020 One type per file: records, interfaces, enums and validators get their own file, in C# and TypeScript"
description: CODE.5 only names classes in .cs files and lets a small record share its user's file; the company convention is one file per class, interface, record, enum, service or validator.
case_id: C-020
rule: /rules/code/code-5-one-responsibility.md
verdict: open
status: draft
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

CODE.5 ("One class per file, named like the file") points the same way but falls short in three places:

- `applies_to` lists `**/*.cs` and `**/*.bicep`, so TypeScript and TSX are not covered.
- It says "class", so records, interfaces, enums and validators are not named.
- Its Boundary lets "a small private type (a record used by one class only)" share the file with its user,
  which is exactly the pattern the owner dislikes.

# Why (open)

Principle P-02 (architecture provides direction) is served by a predictable place for every type: a reader and an
agent find `OrderValidator` by file name, a diff touches one responsibility, and a mixed file does not quietly grow.
Research on coding agents shows no proven preference for fewer or more files (Kang et al., EMNLP 2024; Li et al.,
ACL 2025), so this is an engineering-quality rule, not an AI-performance claim.

Proposed change to CODE.5:

- Rule: "One type per file, named like the file: class, interface, record, enum, service, validator, and in
  TypeScript a component, hook or exported type. A service has many methods; the types it uses live next to it
  in their own files."
- `applies_to`: add `**/*.ts` and `**/*.tsx`.
- Boundary: shrink to a type nested inside its only user and private to it (a nested private enum or helper
  record), not a sibling top-level type in the same file. Tiny file-per-type is not a goal in itself: do not
  add an interface or wrapper only to justify a file.
- Reviewer note: `minor`. On a touched mixed file, ask for the types the diff adds or changes to be split out,
  not for a sweep refactor of the whole file.

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

# Not verified

Whether the .NET analyzer `SA1402` (file may only contain a single type) or an ESLint rule such as
`max-classes-per-file` could enforce this as a gate; the existing mixed files in repos would need a baseline
first. The wording of the narrowed Boundary is a suggestion for the owner to confirm.

[^origin]: repo owner feedback, 2026-10-26
