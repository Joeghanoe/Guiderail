---
type: Gate
title: "OpenAPI drift check (DEL.5)"
description: openapi-drift.py fails a PR whose committed OpenAPI snapshot differs from the document the build generates.
tool: harness/tools/code/openapi-drift.py
owner: team:teamvalue-aicoe
status: stable
tags: [api, openapi, contracts]
---

# Coverage

Any repo that commits an OpenAPI snapshot: the pipeline builds, takes the generated document from the build output and compares it with the snapshot. Reports operations added and removed, and whether anything else changed.

# Blind spots

It does not prove the document is generated rather than hand-written, that operations are complete (operation ids, response types, examples), or that callers still work. A repo without a committed snapshot is covered by review of the build step only.

# Complementary checks

Contract tests for a spec-first API. Review of [DEL.5](../rules/delivery/del-5-the-api-contract-is-generated.md) points 1 to 6.

# Failure behaviour

Exit 1 with the operations added and removed and the instruction to regenerate and commit.

# Exception route

None for drift: regenerate the snapshot. A repo that deliberately commits no snapshot says so in its `AGENTS.md`.

# Refresh trigger

A new stack's generator, or a change to DEL.5.
