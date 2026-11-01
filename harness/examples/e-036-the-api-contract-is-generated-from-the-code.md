---
type: Example
title: "E-036 The API contract is generated from the code, not kept by hand"
description: An API generates its OpenAPI specification directly from code during the build, eliminating manually maintained files that drift.
example_id: E-036
rule: /rules/delivery/del-5-the-api-contract-is-generated.md
verdict: violation
status: draft
tags: [api, openapi, build, ai-readiness]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-31T12:00:00Z }
---

# Situation

A backend service exposes HTTP endpoints consumed by frontends, client integrations, and AI tools. The repository relies on a hand-written `openapi.yaml` that has drifted out of sync with recent route changes.

# Why (verdict)

Manually updated API specifications inevitably drift the moment an endpoint changes. Code must be the single source of truth: OpenAPI documents should be generated offline during build time (DEL.5). If committed for client code generation, CI should verify that the generated spec matches the committed snapshot.

# Compliant pattern

The generator runs as part of the build, needs no running host or secrets, writes the file into the build output, and a CI step compares it with the committed snapshot.

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

A worker or batch job with no HTTP callers has no contract to generate. A spec-first API may keep the hand-written spec if its code is verified against it by contract tests.
