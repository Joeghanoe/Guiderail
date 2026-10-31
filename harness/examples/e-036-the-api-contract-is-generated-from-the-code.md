---
type: Example
title: "E-036 The API contract is generated from the code, not kept by hand"
description: A service publishes its OpenAPI document from its own code on every build, offline, instead of a hand-maintained file that drifts.
example_id: E-036
rule: /rules/delivery/del-5-the-api-contract-is-generated.md
verdict: violation
status: draft
tags: [api, openapi, build, ai-readiness]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-31T12:00:00Z }
---

# Situation

A service exposes several HTTP endpoints. Its callers (a frontend, another team's integration, an AI agent) need the contract. The repo has
an `openapi.yaml` written by hand once, and the endpoints have changed since.

# Why (verdict)

A document someone keeps in step by hand is wrong the first time someone forgets, and nothing tells them. DEL.5 asks for the opposite
direction: the code is the source and the document is its output, produced by the build, offline, so every build has a current one and a
pipeline can publish it. Where a copy is committed so a frontend can generate its client, a check regenerates and compares, so a change to
the contract shows up in the pull request diff instead of in a caller's incident.

# Compliant pattern

The generator runs as part of the build, needs no running host or secrets, writes the file into the build output, and a CI step compares it
with the committed snapshot.

## Good example

```xml
<!-- ASP.NET Core: the document is produced by the build, from the endpoints -->
<PackageReference Include="Microsoft.Extensions.ApiDescription.Server" Version="10.*" PrivateAssets="all" />
<PropertyGroup>
  <OpenApiGenerateDocuments>true</OpenApiGenerateDocuments>
  <OpenApiDocumentsDirectory>$(MSBuildProjectDirectory)/../../build</OpenApiDocumentsDirectory>
</PropertyGroup>
```

```json
{ "scripts": { "openapi": "bun run src/openapi.ts > build/openapi.json", "build": "bun run openapi && vite build" } }
```

```bash
# CI: regenerate, compare with the committed snapshot, fail on drift
python3 -I tools/code/openapi-drift.py --generated build/openapi.json --committed docs/openapi.snapshot.json
```

## Bad example

```yaml
# docs/openapi.yaml, written by hand in the first sprint, edited when someone remembers
paths:
  /api/menus:
    post: { summary: "Create a menu" }   # the service now also has /api/menus/{id}/publish and a changed request body
```

# Boundary

A worker or batch job with no HTTP callers has no contract to generate. A spec-first API may keep the hand-written spec if its code is
verified against it by contract tests.
