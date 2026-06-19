---
name: github-pipelines
description: GitHub Actions workflow authoring — reusable workflows, DTAP environment gating, OIDC Azure auth, composite actions, secrets management, and naming conventions.
---

# GitHub Actions Pipeline Writing

## When to Use

- Creating or editing `.github/workflows/*.yml` workflow files
- Designing multi-environment DTAP (Development, Test, Acceptance, Production) deployments
- Writing reusable workflows or composite actions
- Configuring environment protection rules and deployment gates
- Setting up OIDC-based Azure authentication

## Rules

### Workflow Structure

Every workflow file has a single top-level responsibility:

| File type         | Responsibility                                                  |
| ----------------- | --------------------------------------------------------------- |
| Trigger workflow  | `on:` event, inputs, calls reusable workflow(s)                 |
| Reusable workflow | `on: workflow_call`, receives inputs/secrets, orchestrates jobs |
| Composite action  | `action.yml` under `.github/actions/`, reusable step sequence   |

- Separate trigger concerns from implementation: trigger workflows are thin; reusable workflows carry the logic
- Always declare `permissions:` at the top level or per-job — never rely on repository defaults
- Use `workflow_dispatch:` with typed `inputs` for manual runs requiring parameters

### Multi-Environment DTAP Pattern

Instead of repeating job blocks per environment, use one of these two approaches:

**Reusable workflow approach** (preferred for DTAP with protection rules):

- Define one reusable workflow that accepts `environment` as an input
- Call it from a trigger workflow once per environment with `needs:` chaining for sequential ordering
- Each call gets its own `environment:` context, triggering the matching GitHub Environment's protection rules

**Matrix approach** (appropriate for parallel fan-out without gates):

- Use `strategy.matrix` with an environment list and `fail-fast: false`
- Combine with `environment: ${{ matrix.env }}` to apply per-environment secrets and protection rules

### Environment Gating

- Declare `environment:` on every deployment job — this is what activates protection rules and audit history
- Configure required reviewers and wait timers on GitHub Environments for Acceptance and Production
- Use environment-scoped secrets and variables rather than repository-level secrets where possible
- Sequential DTAP: express ordering with `needs:` — each environment job depends on the previous one

### Secrets and Variables

- Never hardcode secrets, tokens, or credentials in workflow YAML
- Reference secrets via `${{ secrets.SECRET_NAME }}` — repository or environment scoped
- Reference variables via `${{ vars.VAR_NAME }}` for non-secret configuration values
- Pass secrets explicitly to reusable workflows via `secrets:` block or `secrets: inherit` when all secrets are needed
- Set `env:` at the job or step level for values needed across multiple steps — avoid repeating inline

### OIDC Azure Authentication

- Use OIDC (federated identity) for all Azure authentication — no service principal secrets
- Required permissions: `id-token: write`, `contents: read`
- Use `azure/login` action with `client-id`, `tenant-id`, and `subscription-id` as variables (not secrets)
- Configure the federated credential in Azure with the correct subject claim (`repo:org/repo:environment:name` for environment-scoped, `repo:org/repo:ref:refs/heads/main` for branch-scoped)
- Log out with `azure/logout` in an `if: always()` step to clean up the session

### Permissions

- Follow least-privilege: declare only permissions the workflow actually needs
- Default to `permissions: {}` (no permissions) and add explicit grants per job
- Declare `id-token: write` only on jobs that perform OIDC authentication
- Never use `permissions: write-all` — enumerate the specific permissions required

### Concurrency

- Add a `concurrency:` group to all deployment workflows to prevent overlapping runs per environment
- Use `cancel-in-progress: false` for deployments (let the running deploy finish, queue the next)
- Use `cancel-in-progress: true` for CI/validation workflows (cancel superseded runs)
- Group key pattern: `${{ github.workflow }}-${{ github.ref }}` or include the environment name for multi-environment workflows

### Reusable Workflows

- Place reusable workflows in `.github/workflows/` with a descriptive name (e.g., `_deploy-service.yml` — leading underscore signals it is not a standalone trigger)
- Declare all inputs with `type`, `description`, and `required` or `default`
- Pass secrets explicitly with `secrets:` block — document which secrets are expected
- Reusable workflows cannot access the caller's environment secrets unless passed explicitly or `secrets: inherit` is used

### Composite Actions

- Place composite actions in `.github/actions/<action-name>/action.yml`
- Use for reusable step sequences that are called from multiple workflows
- Composite actions run in the caller's job context — they share the workspace and environment
- Keep composite actions under ~20 steps; split into multiple actions if larger
- Prefer composite actions over shell scripts for logic that benefits from GitHub's step visibility

### Step Conventions

- Give every step a descriptive `name:` — it appears in the GitHub Actions UI log
- Use `if: always()` on cleanup steps (logout, artifact upload on failure) to ensure they run
- Inline `run:` scripts should be under 15 lines; extract longer scripts to files in the repository and call via `run: bash .github/scripts/my-script.sh`
- Use `shell: bash` explicitly on cross-platform workflows
- Prefer verified, pinned actions (`uses: actions/checkout@v4`) over inline scripts for common operations

### Naming Conventions

| Element            | Pattern                                                                           |
| ------------------ | --------------------------------------------------------------------------------- |
| Workflow file      | Lowercase with hyphens: `deploy-api.yml`, `ci.yml`, `_reusable-deploy.yml`        |
| Job id             | Lowercase with hyphens: `build`, `deploy-development`, `integration-test`         |
| Step name          | Sentence case, action phrase: `Build solution`, `Deploy to Development`           |
| Input/secret names | SCREAMING_SNAKE_CASE: `AZURE_CLIENT_ID`, `ENVIRONMENT_NAME`                       |
| Environment names  | Match Azure DevOps conventions: `development`, `test`, `acceptance`, `production` |

### Pipeline Triggers

- Use `workflow_dispatch:` for pipelines intended to be triggered manually or by other workflows
- For CI, scope `push:` and `pull_request:` triggers to relevant `paths:` and `branches:`
- Exclude documentation, changelog, and workflow definition paths from CI triggers
- Use `pull_request_target:` only when cross-fork access is explicitly needed — it runs with elevated permissions

## Anti-Patterns to Reject

1. Repeating job blocks per environment instead of using reusable workflows or matrix strategy
2. Hardcoded secrets, tokens, or credentials anywhere in YAML
3. Using `permissions: write-all` — always enumerate specific permissions
4. Missing `concurrency:` on deployment workflows, allowing overlapping deploys
5. Missing `environment:` on deployment jobs — bypasses protection rules and audit trail
6. Using `GITHUB_TOKEN` for operations that require cross-repo access or elevated scopes — use a GitHub App token or PAT stored as a secret
7. Inline `run:` scripts longer than 15 lines that should be composite actions or checked-in scripts
8. Using `secrets: inherit` in reusable workflows without documenting which secrets are expected
9. Skipping `azure/logout` after OIDC authentication — leaves the session open for subsequent steps
10. Unpinned action versions (`uses: actions/checkout@main`) — pin to a specific version tag for reproducibility
