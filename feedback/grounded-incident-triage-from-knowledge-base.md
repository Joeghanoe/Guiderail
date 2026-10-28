---
type: Case
title: "C-NNN Incident triage grounded in live evidence and the support desk's solution articles"
description: Idea only - move support-desk triage up the automation ladder by grounding every triage in read-only evidence plus the existing knowledge base, measured by an eval, with humans deciding.
case_id: C-NNN
rule: /rules/harness/h-2-repeated-work-moves-up.md
verdict: automation-candidate
status: draft
tags: [incidents, triage, support-desk, knowledge-base, eval, idea]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-23T00:00:00Z }
sources:
  - id: evidence
    resource: harness@feature/harness-okf:playbooks/triage-incident.md
  - id: requirement
    resource: "a support desk that keeps its operational knowledge as solution articles in an ITSM tool (e.g. Freshservice)"
---

# Situation

Phase: **idea**. Nothing here is decided or built.

Support desks triage the same kinds of incidents again and again, often closing them with a workaround
(restart, clear a queue) rather than a structural fix. The harness already has a read-only triage playbook
(`triage-incident.md`, status draft) and the wrappers to read customer environments, but triage only
happens when someone asks an agent in a session.[^evidence] The support desk already keeps its known
causes and workarounds as solution articles in its ITSM tool.[^requirement]

# Why (verdict)

`automation-candidate` under H.2 (P6, P12, P13): triage is repeated work with a stable shape, and the
harness review loop (cases as labelled data, `eval.py` as held-out evaluation, thresholds as gate,
feedback as new labels) can be reused for it rather than training a model.

The idea, in steps up the ladder:

1. **Grounded triage.** The agent runs the triage playbook read-only, then looks up solution articles.
   Live evidence says *what is happening*; articles say *what it means and what to do*. Every claim in the
   report cites a query output or an article ID. Each triage ends in one outcome:
   - *Covered* - evidence matches an article.
   - *Contradicted* - an article seems to apply but the evidence does not fit it (possibly stale).
   - *Not covered* - no article fits; the agent says so and drafts an article for a human to publish.
2. **Measurable groundedness.** A deterministic check confirms that cited article IDs exist and quoted
   evidence appears in the saved outputs. Past incidents, anonymized (SEC.2), become replayable eval cases
   scored on class, root cause and groundedness.
3. **Auto-drafted triage (later).** An alert or new ticket starts the playbook headlessly and posts a draft
   as a work note. A human accepts or corrects it.
4. **Recurrence moves up.** A repeated incident fingerprint (exception type, operation, resource, result
   code) or a repeatedly applied workaround article becomes a structural fix: code fix with a layer 0/1
   test (T.4), roll forward (DEL.1), alert (OBS.2), honest health check (OBS.1).

Boundaries that hold throughout:

- Articles, tickets and log text are data, never instructions (SEC.1); a command in an article is written
  down for a human, never run (CLD.2).
- The agent never edits or publishes articles, closes tickets, or changes an environment (CLD.1, CLD.2).
- Read access to the ITSM tool goes through a read-only harness wrapper limited to solution articles; it
  refuses tickets, requesters and agents (SEC.2). Changes to the harness go through a PR (H.1).
- Articles stay in the ITSM tool; harness cases keep only project-agnostic patterns.

# Open questions for a human

- Is this worth pursuing, and for which customer as a pilot?
- Read-only API access to the knowledge base: per customer or per tenant, who requests and owns it?
- Ticket intake for auto-drafting: a narrow read wrapper or a push from the ITSM tool or alerting into a
  pipeline? Where does it run (pipeline or scheduled agent)?
- Where do draft articles land: a draft state in the ITSM tool or next to the triage report?
- Success measures: agreement with the human verdict, drafts accepted unchanged, time to triage,
  recurrence rate per fingerprint.

# Not verified

- The ITSM tool's API and its permission model for article-only read access.
- How much of a real knowledge base covers real incidents; a pilot of about 10 past incidents would measure
  it.
- The review eval itself last ran with a pass rate of 0.0 (`tools/review/history.jsonl`, 2026-10-20), which
  points to a runner or engine problem; a triage eval reusing it depends on that being fixed first.
- That the eval runner can be shared between review and triage instead of copied (H.2).

[^evidence]: Current triage playbook and harness tooling
[^requirement]: Support desk knowledge base as solution articles
