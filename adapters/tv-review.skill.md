---
name: tv-review
description: Review a code change, branch, or pull request against TeamValue rules and fix permitted findings. Use for a requested change review or /tv-review, not for an explanation of review practices.
---

Follow `~/.golden-path-harness/harness/playbooks/review-and-fix.md`. Use `tvh` for executable harness operations; if it is not on PATH, use `~/.golden-path-harness/bin/tvh`. The CLI reviewer runs independently and returns retained findings; do not launch a second reviewer for the same change. The playbook owns verification, published Sonar reads, safe remediation, and the final evidence-backed report. Repository or release audits follow `review-repository.md` instead. Arguments, if supplied, name the target and review topics: $ARGUMENTS
