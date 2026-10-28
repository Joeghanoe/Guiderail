---
type: Playbook
title: Process feedback on the harness
description: Turn a correction, a rejected finding or a missed defect into a proposed case, and decide what the harness should learn.
tags: [harness, feedback]
status: stable
---

# Sources of feedback

| Source | Signal |
|---|---|
| A session | The user corrects output that came from a rule |
| A PR | A review thread closed as `wontFix` or `byDesign` (wrong finding); `fixed` (right finding) |
| DEV or production | A defect that review and tests did not catch |
| Repetition | The same task done a second time (H.2) |

# Steps

1. Find the rule and the cases involved. If no rule was involved, it is not harness feedback.
2. Decide what kind of feedback it is:

| Feedback | Proposal |
|---|---|
| "This finding is wrong here" | A `boundary` case: when the rule does not apply, and why. The rule stays. |
| "You missed this" | A `violation` case with the bad code; if a tool could decide it, propose an analyzer or check (H.2). |
| "The rule is wrong" | Argue with the principle and the existing cases first. If the case still stands, propose a rule change in a PR on the harness repo, citing the cases. |
| Contradicts a principle or a hard rule (SEC.*, CLD.*) | A `rejected` case with the reason, so it is not raised again. |
| The same task again | An `automation-candidate` case: the playbook or script it should become. |

3. Write the case from `/templates/case.md` into `~/.harness-feedback/`: `status: draft`,
   `generated` with your actor, no `verified`. A human reviews it and can run
   `python3 -I ~/.harness/tools/harness/bundle.py submit-feedback <draft.md>` to prepare a local branch and
   worktree. A human reviews, commits, pushes and opens the PR.
4. Check it does not contradict a human-reviewed case. If it does, say which one and why this differs; never
   overwrite it.
5. Tell the user what you proposed; a human verifies or rejects it. Git history records the change.
