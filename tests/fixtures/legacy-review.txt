---
name: tv-review
description: Review a code change, branch, or pull request against TeamValue rules and fix permitted findings. Use for a requested change review or /tv-review, not for an explanation of review practices.
---

Review the changes between `HEAD` and an established baseline across two independent axes:

1. **Standards**: Conformance to TeamValue rules (`tvh review`) and the Fowler code smell baseline as judgment calls (Mysterious Name, Duplicated Code, Feature Envy, Primitive Obsession, Shotgun Surgery, Speculative Generality).
2. **Spec**: Conformance to originating requirements (missing criteria, partial implementations, scope creep).

## Process
Follow `~/.golden-path-harness/harness/playbooks/review-and-fix.md`.
1. **Pre-flight Gate**: Run `tvh verify --repo .`. A failing gate blocks review.
2. **Independent Review**: Run `tvh review --repo . --baseline <baseline>`.
3. **Report Two Axes**: Present `## Standards` and `## Spec` side-by-side without cross-axis reranking.
4. **Safe Remediation**: Apply permitted high-confidence fixes; report others for human decision.
The agent never approves a PR; merge decisions remain with human reviewers (CLD.2). Arguments, if supplied, name the target and review topics: $ARGUMENTS
