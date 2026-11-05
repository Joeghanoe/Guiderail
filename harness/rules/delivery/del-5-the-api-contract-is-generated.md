---
type: Rule
title: "DEL.5 The API contract is generated from the code at build time, never written by hand"
description: Every HTTP API publishes an OpenAPI document generated from its own code, offline, on every build and written to the build output, and a check fails when a committed copy has drifted.
rule_id: DEL.5
principle: [/principles/p-06-automation-by-default.md, /principles/p-13-ai-first-and-colleague-usable.md, /principles/p-11-standards-enable-innovation.md]
tags: [delivery, api, openapi, contracts, ai-readiness]
applies_to: ["**/*.cs", "**/*.csproj", "**/*.ts", "**/*.py", "**/openapi*.json", "**/swagger*.json", "**/*.yml"]
enforced_by: [gate:/gates/openapi-drift.md, review]
severity: major
status: stable
approval_commit: 81d380d
sources:
  - id: precedent
    resource: a TeamValue shared package that reflects over a built Azure Functions app and writes swagger.json into the build output on every build, offline, with no host or settings
  - id: origin
    resource: FoodApp portal build (2026-10-31): the plan promised an OpenAPI snapshot and a CI check; nothing in the harness asked for it, so the API shipped without a contract and the frontend types were written by hand
---

# Rule

An API is any service that other code or other people call over HTTP: an app, a function app, a gateway-fronted backend. Its contract is an OpenAPI 3 document, and that document is an **output of the code**, never an input someone keeps in step by hand.

1. **Generated from the code.** The routes, parameters, request and response types, status codes and the security scheme come from the code and its annotations or types (reflection, framework metadata, a schema library). A hand-written spec is allowed only for a spec-first API, and then the code is checked against it (contract tests), so one side is always generated or verified.
2. **At build time, offline.** Building produces the document with no running host, no network and no secrets, so CI and an agent can get it from a plain build. It lands in the build output next to the artifact (`bin/.../swagger.json` or `openapi.json`, `dist/`, `build/`) and the pipeline publishes it as an artifact. The generator is a no-op for projects that are not APIs, so one blanket reference in a shared props file or template is safe.
3. **Same pipeline as the runtime document.** If the service also serves its document (`/openapi.json`, a Swagger UI), the build-time document and the served one come from the same generation code, so they cannot disagree.
4. **One place for metadata.** Title, version, description and servers come from one class or file, not from a copy per environment.
5. **Operations are complete enough to call.** Every operation has a stable `operationId`, a summary, the response type for each status it returns, and the error body (the OBS.3 error-code catalogue). Examples where a value is not obvious (AI agents call APIs from this document).
6. **Consumers read the generated file.** Frontend types or clients, API management imports, contract tests and agents are generated from it, not retyped.
7. **A drift check where a copy is committed.** When a snapshot is committed (a frontend in the same repo generates its client from it, or reviewers want to see contract changes in the diff), CI regenerates the document and fails when it differs from the committed copy ([openapi-drift.py](../../tools/code/openapi-drift.py)). A breaking change (a removed operation or a changed required field) is then visible in review.

# Stack notes

The rule is stack-neutral; only the generator differs. Each stack gets one command that writes the file offline.

| Stack | Generator (examples) | Where the build writes it |
| --- | --- | --- |
| ASP.NET Core minimal APIs and controllers | `Microsoft.AspNetCore.OpenApi` (`AddOpenApi`) with the build-time document generation of `Microsoft.Extensions.ApiDescription.Server`; or the Swashbuckle CLI (`swagger tofile`) | the build output or a configured documents directory |
| .NET isolated Azure Functions | a build-only package that reflects over the built assembly and runs the OpenAPI extension's own pipeline | `$(TargetDir)swagger.json`, on every build |
| TypeScript | NestJS `@nestjs/swagger` (`SwaggerModule.createDocument`), Fastify `@fastify/swagger`, Hono or Express with zod-to-openapi, `tsoa` from types; run by a script such as `bun run openapi` that builds the app object without listening | `build/openapi.json` (the script is part of `build`) |
| Python | FastAPI `app.openapi()` or Django REST `drf-spectacular`, dumped by a small module run in CI | `build/openapi.json` |
| Anything else | the framework's own metadata export; if there is none, the API is spec-first and the code is verified against the spec | a fixed path the pipeline publishes |

# Boundary

A service nobody calls over HTTP (a worker, a batch job, a library) has no contract to generate. A prototype whose design says "no consumers yet" is exempt until it has one. A third-party API you only consume is described by its owner, not by you.

# Check

`tools/code/openapi-drift.py --generated <fresh> --committed <snapshot>` fails with the operations added and removed. Review confirms that the build produces the file, that operations are complete (point 5), and that a hand-written spec has contract tests behind it.
