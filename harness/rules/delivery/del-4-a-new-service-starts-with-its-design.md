---
type: Rule
title: "DEL.4 A new repo or service starts with its design, written before the code"
description: A solution design, an ADR for each decision that is hard to reverse, the repo's own AGENTS.md and a verify command exist before the first feature code, and the code follows them.
rule_id: DEL.4
principle: /principles/p-02-architecture-provides-direction.md
tags: [delivery, architecture, greenfield, documentation]
applies_to: ["**"]
enforced_by: [review, playbook:start-greenfield]
severity: major
status: draft
sources:
  - id: origin
    resource: first greenfield evaluation run (2026-10-29): all functional checks passed, yet no design, no ADR, no repo AGENTS.md and no verify command were produced
---

# Rule

When a repo or a service is new, these exist before the first feature code, and are kept true as the code
changes:

- **`docs/solution-design.md`** from `templates/solution-design.md`: the one question the service answers,
  its components and what each depends on, how data flows and where it is stored, how it fails, what it
  reports, what it does not do. The code follows it; a divergence is fixed in one of the two in the same change.
- **One ADR per decision that is hard to reverse or likely to be questioned again** (stored data layout,
  retention, identity of a run, failure semantics, a technology choice), in `docs/adr/`. The format and the
  numbering belong to the repo's ADR convention or Vegviser's `vegviser-adr` skill; the harness defines none.
  Where neither exists, a short `NNNN-title.md` with context, decision and consequences is enough.
- **The repo's own `AGENTS.md`** from `templates/repo/AGENTS.md`: layout, vocabulary, current decisions,
  how a change crosses boundaries (CODE.7), how to verify, when to ask. The base file is not a substitute.
- **`scripts/verify.sh`, `Directory.Build.props` and `BannedSymbols.txt`** (T.1, T.2), so "done" has a command.

# Boundary

A task that states its own architecture or says "choose your architecture" still needs the design: the choice
is the content. A throwaway spike says it is a spike and writes none of this. The design is as long as the
service needs; one page is normal, and prose that restates the code is a finding.
