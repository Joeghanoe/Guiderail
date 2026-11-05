# Centralized Agentic Workflows with `gh-aw` & GitHub Actions

> **Summary**: Lessons learned while setting up an organization-wide `/golden-path-review` pull request review workflow using GitHub Agentic Workflows (`github/gh-aw`), centralized in a single repository (`Guiderail`) and consumed across downstream repositories (`BrewBook`, etc.).

---

## 1. Architectural Overview

The goal was to establish a single source of truth for engineering standards and code review without duplicating workflow definitions, prompts, or scripts across every project repository.

```
┌────────────────────────────────────────────────────────┐
│ Central Repository: Joeghanoe/Guiderail (Public)       │
│                                                        │
│  .github/workflows/golden-path-review.md               │
│         │ (compiled via `gh aw compile`)               │
│         ▼                                              │
│  .github/workflows/golden-path-review.lock.yml         │
│  - Self-contained prompt (`inlined-imports: true`)     │
│  - Copilot CLI engine with sandboxed MCP tools         │
│  - Safe outputs: line comments, reviews, reactions     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ uses: Joeghanoe/Guiderail/...@main
                           │ (Reusable Workflow / workflow_call)
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Downstream Repository: Joeghanoe/BrewBook              │
│                                                        │
│  .github/workflows/review.yml (19-line caller relay)   │
│  - Triggers on: `issue_comment: [created]`             │
│  - Filters for: `/golden-path-review` on PRs           │
│  - Forwards execution to central Guiderail lockfile    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Key Learnings & Pitfalls Solved

### Pitfall 1: Public vs. Private Repository Visibility Mismatch
* **Symptom**: `error parsing called workflow ... : workflow was not found`.
* **Root Cause**: In GitHub Actions security architecture, a **Public repository can NEVER call a reusable workflow in a Private repository** (to prevent private workflow source code from leaking into public action logs). Even when repository Settings → Actions → General → Access is set to allow access across the account, this restriction is hard-enforced.
* **Resolution**: The central repository hosting the reusable workflow must match or exceed the caller's visibility. For public downstream repositories (like `BrewBook`), `Guiderail` must be set to **Public**.

---

### Pitfall 2: Runtime Imports Fail Cross-Repository (`inlined-imports: true`)
* **Symptom**: 
  ```text
  ERR_API: Failed to process runtime import for .github/workflows/golden-path-review.md:
  ERR_SYSTEM: Runtime import file not found: /home/runner/work/BrewBook/BrewBook/.github/workflows/golden-path-review.md
  ```
* **Root Cause**: By default, `gh-aw` generates a runtime import macro in the compiled lockfile:
  `{{#runtime-import .github/workflows/golden-path-review.md}}`
  When executed within the central repo, this file exists locally. But when called from an external repository via `workflow_call`, the runner workspace only checks out the caller repository, where the `.md` file does not exist.
* **Resolution**: In the central workflow's frontmatter, add:
  ```yaml
  inlined-imports: true
  ```
  Running `gh aw compile` will bake the entire prompt instructions directly into the environment variables (`GH_AW_PROMPT_CONTENT_*`) of the generated lockfile, making it 100% self-contained with no local file dependencies at runtime.

---

### Pitfall 3: Permission Elevation Blocking in Reusable Workflows
* **Symptom**:
  ```text
  Error calling workflow '.../golden-path-review.lock.yml@main'.
  The nested job 'activation' is requesting 'actions: read, discussions: write, issues: write, pull-requests: write',
  but is only allowed 'none'.
  The nested job 'conclusion' is requesting 'checks: read', but is only allowed 'none'.
  ```
* **Root Cause**: A reusable workflow cannot grant permissions that the caller workflow has not explicitly authorized. If the caller (`review.yml`) lacks a top-level `permissions:` block or defaults to read-only, nested jobs requiring write or specific read scopes will immediately fail at workflow startup.
* **Resolution**: The caller workflow must explicitly declare all permissions needed by the agentic pipeline:
  ```yaml
  permissions:
    actions: read
    checks: read
    contents: read
    discussions: write
    issues: write
    pull-requests: write
    copilot-requests: write
  ```

---

### Pitfall 4: `issue_comment` Only Evaluates Against the Default Branch
* **Symptom**: Workflow runs fail to trigger or report `workflow was not found` during PR testing on new branches.
* **Root Cause**: In GitHub Actions, `issue_comment` events are **always evaluated against the repository's default branch (`main`)**, not the pull request's head branch.
* **Resolution**:
  1. The caller workflow file (`.github/workflows/review.yml`) must be merged into `main` of the consuming repository for `/golden-path-review` PR comments to execute.
  2. For pre-merge branch testing, add `pull_request: types: [opened, synchronize]` to the caller workflow temporarily.

---

### Pitfall 5: Passing Secrets Across Repositories
* **Symptom**: Agent cannot authenticate with Copilot or GitHub APIs when invoked from an external repo.
* **Resolution**: Ensure the caller workflow passes secrets through to the central reusable workflow:
  ```yaml
  jobs:
    review:
      uses: Joeghanoe/Guiderail/.github/workflows/golden-path-review.lock.yml@main
      secrets: inherit
  ```

---

## 3. Reference Implementation: Downstream Repo Caller

To enable `/golden-path-review` in any other repository across the organization, add this single file to that repository's `main` branch:

**`.github/workflows/review.yml`**:
```yaml
name: Golden Path Review
on:
  issue_comment:
    types: [created]

permissions:
  actions: read
  checks: read
  contents: read
  discussions: write
  issues: write
  pull-requests: write
  copilot-requests: write

jobs:
  review:
    if: github.event.issue.pull_request != null && startsWith(github.event.comment.body, '/golden-path-review')
    uses: Joeghanoe/Guiderail/.github/workflows/golden-path-review.lock.yml@main
    secrets: inherit
```

---

## 4. Operational Checklist for Central Repo Maintenance

When modifying review rules, playbooks, or instructions in `Guiderail`:

1. Edit `.github/workflows/golden-path-review.md`.
2. Ensure `inlined-imports: true` is preserved in the frontmatter.
3. Recompile the lockfile:
   ```bash
   gh aw compile
   ```
4. Verify with `gh aw validate`.
5. Commit and push `.md`, `.lock.yml`, and the `.yml` alias to `main`.
6. All downstream repositories instantly inherit the updated review standards without any changes to their individual codebases.

---

## 5. Wiring the Deterministic Harness & Dynamic Rules

A review agent requires more than just high-level prose; it needs the exact rules and precedent examples that apply to the changed files, plus execution evidence from deterministic repository checks:

1. **Mounting the Harness via `steps:`**:
   Using `actions/checkout`, the central workflow checks out `Joeghanoe/Guiderail` into `.harness` inside the runner workspace before the agent runs.

2. **Pre-flight Deterministic Gates (`T.1`)**:
   If the repository has a `./scripts/verify.sh` test script, it is run first. If it fails, the agent reports this as a blocker finding under rule `T.1` without approving.

3. **Dynamic Rule Selection (`bundle.py select`)**:
   `bundle.py select` reads the PR's `changed.txt` and generates `/tmp/gh-aw/harness/selected.json`. The agent opens this file to inspect the exact rules and precedents relevant to the change, avoiding hallucinated or irrelevant rule citations.

4. **Two-Axis Assessment**:
   Findings are evaluated and formatted following `.harness/skills/engineering/code-review/REVIEW-CHANGE.md` across both **Standards** and **Spec** axes.
