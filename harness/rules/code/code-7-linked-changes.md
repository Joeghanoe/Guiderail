---
type: Rule
title: "CODE.7 Files that must change together are linked: listed in the change map, and checked where a check is possible"
description: A name, code or format that two files depend on across code, docs, infra, config and queries is listed in the repo's change map, and a test or gate fails when one side changes without the other.
rule_id: CODE.7
principle: /principles/p-02-architecture-provides-direction.md
tags: [code, docs, infra, contracts, change-impact]
applies_to: ["**/*.cs", "**/*.md", "**/*.bicep", "**/*.tf", "**/*.kql", "**/*.yml", "**/*.json", "**/*.jsonc"]
enforced_by: [review]
severity: major
status: draft
sources:
  - id: origin
    resource: a repo AGENTS.md section "Follow a change across boundaries", with tests that pin docs and data files to the code
---

# Rule

CODE.4 writes a name once inside the code. This rule covers the names that cannot be written once because
they live in files of different kinds: an event name in code and in an alert query, an error code in code
and in a runbook, a config field in a record and in every config file, a role in a template and in a
joiner runbook. Nothing breaks at build time when one side changes, so the break shows up later and quietly:
an alert that never fires, a runbook that misses a code, a config file the worker rejects on its first run.

- The repo's `AGENTS.md` has a section "Follow a change across boundaries": per kind of change, every file
  it touches. Each entry is marked **checked** (naming the test or gate) or **documented**.
- Where both sides can be read at build time, a test or gate reads them and fails when they disagree: the
  doc page is parsed for every code in the catalog, every config file is parsed by the production parser,
  every name an alert query uses exists as a constant in the code.
- A **documented** entry is a known gap, not a finished one. Turn it into a check when it bites (H.2).
- A diff that changes one side of a listed pair and not the other is a finding, with both paths as evidence.

# Boundary

A pair that cannot be checked at build time (a message to a customer, a setting in another tenant, a manual
step in a partner's portal) stays **documented**. The change map still lists it, so a reviewer can ask for it.
