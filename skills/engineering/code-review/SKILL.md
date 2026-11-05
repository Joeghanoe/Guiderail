---
name: code-review
description: Review a branch, pull request, or local diff against repository standards and originating requirements. Use for an actual change or repository review, not a conceptual question about review practices.
---

# Review changes independently

Establish the target, explicit baseline, intended source scope and originating requirements. Never guess the target branch. Distinguish standards findings from missing, partial or conflicting requirements. If no spec is available, report spec coverage as unassessed.

Read [review and safe remediation](REVIEW-AND-FIX.md) for a change review. It owns gate ordering, independent reviewer execution, finding validation and permitted fixes. Failed verification blocks a clean review. Untracked intended files leave scope incomplete. Do not launch duplicate reviewers.

Read [change-review judgment](REVIEW-CHANGE.md) when assessing evidence against selected rules. For an explicitly requested repository or release assessment, use [repository review](REVIEW-REPOSITORY.md) instead. Do not load both modes by default. Code smells are subordinate quality heuristics; cite a canonical rule for a finding, otherwise label it a quality note.

```bash
tvh verify --repo .
tvh review --repo . --baseline <target-ref> --engine <authorized-engine>
```

Keep the native findings contract unchanged. The human report separates Standards from Spec and records scope, evidence, fixed findings and unresolved decisions. Hand permitted fixes back with fresh verification evidence. A human accepts findings and approves or merges the PR.
