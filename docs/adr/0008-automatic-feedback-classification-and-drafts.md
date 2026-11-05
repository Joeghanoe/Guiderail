# ADR 0008: Automatic feedback classification and drafts

- **Status:** Draft; owner direction recorded, implementation pending
- **Date:** 2026-10-31
- **Owner:** joeghanoe, under ADR 0007 decision 2
- **Scope:** Capture, classify and route corrections, including new conventions and missing requirements
- **Depends on:** ADR 0002, ADR 0003, ADR 0004, ADR 0005, ADR 0007
- **Extends:** H.1 and the process-feedback playbook; their implementation must be updated separately

## Context

Meaningful corrections should become durable feedback without requiring the user to classify them or ask for a draft. The current process only accepts feedback tied to an existing rule. This excludes new conventions and missing requirements, or encourages attaching them to an unrelated rule.

The early-return draft in [processed early-return draft](../feedback/processed/code-return-early-no-nested-else-minimal-ternaries.md) demonstrates the gap. It proposes a control-flow convention but points to CODE.3 because the format requires an existing rule.

## Existing decisions and overlap

This ADR extends the intake process rather than defining another approval or evaluation process.

| Already present | Authority | Extension in this ADR |
| --- | --- | --- |
| Capture rule-related corrections as draft examples; humans accept them | [H.1](../../harness/rules/harness/h-1-feedback-becomes-an-example.md), [process-feedback](../../harness/playbooks/process-feedback.md) | Accept corrections without an existing rule and classify their destination automatically |
| Review changes before changing standards | [ADR 0002](0002-agentic-sdlc-and-harness-principles.md), decision 6 | Prepare proposals automatically within that boundary |
| Backlog/specification ownership and human approval | [ADR 0003](0003-knowledge-to-code-boundary.md), [ADR 0004](0004-harness-scope-and-boundaries.md) | Route missing requirements to their owner without creating another system of record |
| Evaluate standards changes and preserve independent evidence | [ADR 0005](0005-evaluation-and-continuous-improvement.md) | Reuse that process when a draft proposes shared guidance |
| Promote recurring work into automation | [H.2](../../harness/rules/harness/h-2-repeated-work-moves-up.md) | Reuse existing automation-candidate handling |

## Decision

Automatically capture explicit, meaningful corrections, classify them and create or update a draft in the existing feedback queue. An existing rule reference is optional. Draft creation does not make the proposal authoritative.

### Capture and classification

The agent captures corrections to its output, newly stated conventions and identified missing requirements. Routine task requests and speculative suggestions are not automatically treated as corrections. Existing PR and defect feedback sources remain supported; scheduled collection of PR threads is separate implementation work.

| Classification | Proposed destination | Example |
| --- | --- | --- |
| Existing rule missed or misapplied | Example linked to the rule | An exception was swallowed despite CODE.2 |
| New shared convention | Harness convention proposal with no rule ID required | The user explicitly requires early returns across company repositories |
| Repository-specific convention | Local AGENTS.md or linked repository guidance | Handlers belong beside their feature in this repository |
| Missing product requirement | Owning specification or acceptance criteria | Export must preserve the active filters |
| Design-system requirement | Owning design-system guidance | Interactive states must support dark mode |
| Recurring task | Existing H.2 automation-candidate process | The same manual verification is needed again |
| Ambiguous or conflicting correction | Unclassified draft with candidate destinations and the conflict | A requested convention conflicts with approved guidance |

The classifier records uncertainty rather than forcing a category. It defaults inferred scope to the current repository. Broader scope requires an explicit user statement or cited authoritative evidence; repetition alone does not establish company policy. Related corrections may link drafts with different owners instead of merging distinct requirements.

### Draft contents and deduplication

Use one intake queue initially, with a general feedback draft format distinct from the existing rule-linked example format. Each draft records:

- A stable identifier, draft status, classification and proposed destination.
- The correction and concrete failure, with minimal source evidence and provenance.
- Proposed guidance or requirement, its inferred scope and the reason for that scope.
- An existing rule reference when applicable, relevant conflicts and unresolved questions.
- The destination owner when known; otherwise an explicit unknown owner.
- Occurrences and review disposition, including links to related or superseded drafts.

Before creating a draft, search for the same lesson within the same scope and destination. Append new evidence to a matching open draft and increase its review priority. A correction that repeats despite accepted guidance indicates an application or retrieval failure; link that guidance rather than propose the same rule again. If the match is uncertain, preserve separate linked drafts.

### Current task and promotion

Apply explicit user corrections to the current task when they are authorized and sufficiently clear. Creating a durable draft must not delay that work. If a correction needs a scope or ownership decision, record it and continue independent work; request clarification before dependent work.

Tell the user briefly which draft was created or updated. Drafts are not loaded as binding guidance, given verified-example status or used to change evaluation thresholds. Classification does not approve a requirement, grant an exception or override an existing rule.

Review uses the existing owner and approval boundaries. An accepted draft becomes the appropriate rule-linked example, proposed rule change, repository guidance update, specification change or design-system change. The owning system remains authoritative. Capture in the local feedback queue does not authorize backlog writes, external messages or automatic edits to those destinations.

## Alternatives considered

| Option | Trade-off |
| --- | --- |
| Keep rule-linked examples as the only intake | Simple, but cannot represent new conventions or missing requirements accurately |
| Append every correction directly to coding standards | Immediate persistence, but mixes requirements with conventions and silently broadens scope |
| Separate intake workflow per destination | Specialized handling, but more machinery before feedback volume justifies it |
| One automatically classified draft queue, chosen | Low capture effort and explicit ownership; requires triage and deduplication |

## Consequences

The user no longer needs to request a retrospective or choose the destination for each correction. Human review remains the promotion constraint. Misclassification and draft backlog are accepted costs; repository scope by default and explicit uncertainty limit their impact.

Implementation must update H.1, AGENTS.base.md, process-feedback, feedback documentation and the draft validation/submission tooling. Existing example drafts remain supported. The current rule-linked example template is used when promoting an applicable draft, without inventing a rule reference for other kinds. This ADR records the decision; it does not implement these changes.

## Acceptance criteria for implementation

- A correction with an existing rule creates or updates a linked draft without a separate user request.
- A new convention without a rule is captured and validated without a placeholder rule reference.
- A missing product or design-system requirement has the correct proposed destination and does not silently alter approved acceptance criteria or shared standards.
- An inferred convention remains repository-scoped unless broader authority is recorded.
- Repeated equivalent feedback updates one open draft; materially different scopes remain separate.
- Ambiguous or conflicting feedback preserves its evidence and uncertainty for review.
- Draft creation leaves authoritative guidance, verified examples and evaluator definitions unchanged.
- Classification evaluations cover each category, non-correction requests, scope errors, conflicts and duplicate handling. Shared-guidance promotion follows the existing evaluation process.
