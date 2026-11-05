---
type: Rule
title: "CODE.10 A derived value has one owner, is never accepted from outside, and says when it becomes consistent"
description: A value computed from other data is calculated in one named place, refused or ignored when a caller supplies it, and the design states whether readers see it immediately or eventually and who must not trust a stored copy.
rule_id: CODE.10
principle: [/principles/p-02-architecture-provides-direction.md, /principles/p-08-observable-by-design.md]
tags: [code, design, consistency, derived-data, hooks]
applies_to: ["**/*.cs", "**/*.ts", "**/*.py", "**/*.md"]
enforced_by: [review]
severity: major
status: stable
approval_commit: 720cdc6
sources:
  - id: origin
    resource: FoodApp portal build (2026-10-31): recipe macros are derived from ingredient lines by a Directus hook. The hook is an action that runs after the response returns, so a read right after a write could still show the previous figure; the first journey tests passed only by luck of timing. The portal now calculates the figures it shows live, and its tests wait for the stored ones.
---

# Rule

A derived value is anything computed from other stored data: a total, a status flag, a macro, a balance, a search index, a denormalised count.

1. **One owner.** The value is calculated in one named place (a function, a hook, a database computation), described in the design. Any second implementation is held equal to the first by shared test vectors ([CODE.7](code-7-linked-changes.md)), not by hope.
2. **Never accepted from outside.** A caller, an import file or a form that supplies a derived value has it ignored or refused, with a notice. A typed number turns a calculated, auditable value into a guess.
3. **Consistency is stated.** The design says, for each derived value, **when** it is right after a write:
   - _in the same transaction_: a reader sees it immediately (a database computation, a synchronous service call, a trigger);
   - _eventually_: a hook, an event, a queue consumer, a change feed, an ORM post-save signal or any "after" callback that runs after the response returns. Treat these as eventually consistent unless the platform documents otherwise and a test proves it.
4. **A reader that needs the current value does not trust the stored copy.** It calculates the value from the source, or waits for the change (an event, a poll with a limit), and the design names which readers may see a stale value and for how long. The user interface never shows a stored derived value right after the user changed its inputs without one of these.
5. **One test states the claim.** A test writes the input and reads the derived value and asserts what it observes: immediately, or after a wait. A test that reads right after a write and passes by luck of timing is a finding.

# Boundary

A value that is cheap and pure (a formatted name, a sum of two fields in a view model) is calculated where it is shown and needs no owner. A value that is recorded on purpose at a moment in time (a snapshot, an invoice total) is not derived; it is data, and it is never recalculated (state that in the design).

# Check

Review reads the design for the derived values, their owner and their consistency; a stored derived value shown in a screen straight after its input changed, or a test that reads right after a write with no wait or proof, is a major finding that cites CODE.10.

# Related guidance

This rule applies [P2 Architecture Provides Direction](../../principles/p-02-architecture-provides-direction.md), [P8 Observable by Design](../../principles/p-08-observable-by-design.md).
