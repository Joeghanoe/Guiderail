---
type: Gate
title: Design check (DEL.4, CODE.8, OBS.3, T.3)
description: design-check.py fails a new repo or service whose design is missing, still a template, or not reflected in the code's structure.
tool: harness/tools/greenfield/design-check.py, called from scripts/verify.sh
owner: team:teamvalue-aicoe
status: draft
tags: [architecture, greenfield, dotnet]
---

# What it checks

Static, no build, no network, a few milliseconds. `generic` profile: a filled `docs/solution-design.md` (D01), at least one ADR (D02), the repo's own filled `AGENTS.md` (D03), `scripts/verify.sh` with format, warnings-as-errors and tests (D04), container registrations in `Program.cs` (D05), no operation, service or handler class constructing a collaborator that implements an interface (D07), and tests that exercise components without the entry point (D09). `service` profile adds two ADRs, source/store/clock interfaces (D06) and the OBS.3 contract: an error-code catalogue, event names and a status or health call (D08). `web-app` profile (an HTTP application) adds two ADRs, at least four interfaces that something implements under any names plus a clock through `TimeProvider` or `IClock` (D06), and an error-code catalogue with a health endpoint (D08), without run events or the source and store role names that suit a batch service.

# Blind spots

It proves that the documents exist and the structure is present, not that either is good or true. A design that restates the template and a registration that registers nothing real pass. A reviewer reads the design and the ADRs; a divergence between design and code is a review finding (DEL.4).
