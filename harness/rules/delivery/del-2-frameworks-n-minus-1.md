---
type: Rule
title: "DEL.2 Frameworks at n-1"
description: Use the current stable framework version or the one before it, never older.
rule_id: DEL.2
principle: /principles/p-11-standards-enable-innovation.md
tags: [delivery, dependencies]
applies_to: ["**/*.csproj", "**/package.json", "**/Directory.Build.props", "**/global.json"]
enforced_by: [review]
severity: minor
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

Runtime and framework versions are the current stable release or the one before it. An older version needs an
upgrade item on the backlog, linked in the PR.
