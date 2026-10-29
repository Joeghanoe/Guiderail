---
name: tv-review
description: Review the current diff against the TeamValue harness rules, show findings readably, and fix the ones the harness allows. Use when the user runs /tv-review or asks for a harness review of a change.
---

Follow `~/.golden-path-harness/harness/playbooks/review-and-fix.md`: the review runs in a subagent, and when the branch has an open PR, Sonar's findings for it are read first. Arguments, if any, name a target (PR, branch or path): $ARGUMENTS
