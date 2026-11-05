---
type: Playbook
title: Process feedback on the harness
description: Turn a correction, a rejected finding or a missed defect into a proposed example, and decide what the harness should learn.
tags: [harness, feedback]
status: stable
---

# Sources of feedback

| Source | Signal |
| --- | --- |
| A session | The user corrects output that came from a rule |
| A PR | A review thread closed as `wontFix` or `byDesign` (wrong finding); `fixed` (right finding) |
| DEV or production | A defect that review and tests did not catch |
| Repetition | The same task done a second time ([H.2](../rules/harness/h-2-repeated-work-moves-up.md)) |

# Steps

1. Find the rule and the examples involved. If no rule was involved, it is not harness feedback.
2. Decide what kind of feedback it is:

| Feedback | Proposal |
| --- | --- |
| "This finding is wrong here" | A `boundary` example: when the rule does not apply, and why. The rule stays. |
| "You missed this" | A `violation` example with the bad code; if a tool could decide it, propose an analyzer or check ([H.2](../rules/harness/h-2-repeated-work-moves-up.md)). |
| "The rule is wrong" | Argue with the principle and the existing examples first. If the example still stands, propose a rule change in a PR on the harness repo, citing the examples. |
| Contradicts a principle or a hard rule (SEC._, CLD._) | A `rejected` example with the reason, so it is not raised again. |
| The same task again | An `automation-candidate` example: the playbook or script it should become. |

3. Write the example from `/templates/example.md` into [feedback](../../feedback): `status: draft`, `generated` with your actor, no `verified`. Principles and hard rules remain authoritative ([H.1](../rules/harness/h-1-feedback-becomes-an-example.md)). A legitimate boundary proposes where a rule does not apply; it does not remove the rule. Write the lesson as a general rule, not the story of the incident. Test: would it make sense to someone who was not there? "Check that no interactive element is covered after a layout change" passes; "check the z-index of the checkout banner from March 4" does not. Prefer, in order: fix the setup, encode it in a check, write the rule, and only last rely on memory. A fact that can change an action (plan, price, status) is fetched, never remembered.
4. Check it does not contradict a human-reviewed example. If it does, say which one and why this differs; never overwrite it.
5. Tell the user what you proposed; a human verifies or rejects it. Git history records the change.

# Human review and submission

Review drafts weekly. Accept an example by assigning an unused example number, setting `status: stable` and adding human `verified` metadata under [H.1](../rules/harness/h-1-feedback-becomes-an-example.md); rejected drafts can be deleted. Accepted examples belong in `harness/examples/`.

After a decision, move the processed source feedback from `feedback/` to `docs/feedback/processed/` and link the resulting examples or the reason it was declined. Keep undecided ideas in the queue. Keep current conventions in [feedback-conventions.md](../../docs/decisions/feedback-conventions.md) and add a brief change-and-rationale summary to [log.md](../log.md). The log uses newest-first `## YYYY-MM-DD` sections with prose list entries; Git remains authoritative. Current conventions are editable as experience changes the decision; update their examples and checks with them. This is not an ADR requirement, and moving a source record does not itself approve a rule or example.

To prepare a draft without changing the active harness checkout, run this before adding `verified`:

```bash
tvh bundle submit-feedback --raw -- ~/.golden-path-harness/feedback/<draft.md>
```

The command validates the draft, creates a local branch and worktree under `~/.golden-path-harness/workspaces/feedback/`, copies it into `harness/examples/`, refreshes the index and stages those two files. It does not contact a remote or create a PR. Review the staged diff, apply the acceptance metadata, run the required checks, then commit, push and open the PR yourself.
