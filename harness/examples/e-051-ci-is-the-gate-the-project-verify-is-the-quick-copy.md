---
type: Example
title: "E-051 CI is the full gate; the quick verify lives outside the repo"
description: A repo gets no scripts/verify.sh of its own; the agent's quick check is kept per project in ~/.golden-path-harness and gaps are proposed to CI.
example_id: E-051
rule: /rules/testing/t-1-done-means-verified.md
verdict: boundary
status: draft
tags: [verification, ci, greenfield]
owner: human:joeghanoe
stale_after: 2027-05-03T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-03T00:00:00Z }
sources:
  - id: requirement
    resource: owner feedback that every repo got a scripts/verify.sh, a second pipeline next to the repo's CI
---

# Situation

`greenfield-init.sh` wrote `scripts/verify.sh` into each repo, and the Stop hook, local runs and CI were meant to share it. That puts a second copy of the pipeline in every repo next to its CI.

# Why (verdict)

CI is the authority and runs the full gate. The agent still needs a fast local check, so it is kept per project in `~/.golden-path-harness/projects/<repo-id>/verify.sh` (`tools/code/project-verify.sh`). When it finds something CI misses, the check is added there; a critical one is proposed to the repo's CI as a diff for a human, never applied by the agent (CLD.2). A `scripts/verify.sh` committed in a repo is not used by the Stop hook.

## Good example

```bash
bash ~/.golden-path-harness/harness/tools/code/project-verify.sh init --profile service .
bash "$(bash ~/.golden-path-harness/harness/tools/code/project-verify.sh path .)" --fast
```

## Bad example

```bash
# a second pipeline in the repo, next to azure-pipelines.yml
cp ~/.golden-path-harness/harness/templates/repo/scripts/verify.sh scripts/verify.sh
```

# Not verified

Tested with stubs (`tests/run.sh`), not against a real repo with CI. Repos that already carry a `scripts/verify.sh` lose the Stop check until `project-verify.sh init` is run for them.
