---
type: Rule
title: "CODE.1 Remove what is not used"
description: Commented-out code, unused usings, packages, settings, files and parameters are deleted, not left behind; version control remembers them.
rule_id: CODE.1
principle: /principles/p-12-continuous-improvement.md
tags: [code, hygiene]
applies_to: ["**/*.cs", "**/*.csproj", "**/*.bicep", "**/*.yml", "**/*.yaml", "**/*.ps1", "**/*.json"]
enforced_by: [review]
severity: minor
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- Code in comments is deleted. If it is needed later, it is in git history.
- An unused `using`, package reference, setting, file, template parameter or pipeline task is removed in the
  same change that stops using it.
- A thing added "for later" or "for the future" is not added. A thing that is kept on purpose carries a
  comment that says why.
- Scaffolding the tool generated (`Function1.cs`, an extra `.gitignore`, sample files) is removed or renamed
  before the PR.
- Before you ask a reviewer "is this used?", search for it yourself.

# Boundary

A framework or platform may require a reference that no code mentions (a analyzer package, a runtime setting
the host reads). Keep it and say why in a comment.
