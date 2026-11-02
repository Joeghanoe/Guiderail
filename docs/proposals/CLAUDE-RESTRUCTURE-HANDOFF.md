# Claude Code handoff: Restructure the Golden Path Harness repository

You are working in an **existing** harness repository. Inspect the real repository before editing. The objective is a minimal, safe reorganization that supports the Golden Path ADRs and cleanly separates harness functionality, adapters, evaluations, infrastructure, and tests. **Do not rebuild the harness or assume paths that do not exist.**

## Read first

- `docs/adr/0001-evolution-of-the-golden-path.md` (proposed company process decision)
- `docs/adr/0002-agentic-sdlc-and-harness-principles.md` (draft, not approved)
- `docs/adr/0003-knowledge-to-code-boundary.md` (draft, not approved)
- Existing repo README, agent rules, install scripts, evaluator runner, adapters, policies, CI files, and tests.

These ADRs describe intent; drafts are **not** approval to weaken governance or deploy changes. If they conflict with established repository decisions, report the discrepancy rather than silently overriding it.

## Desired conceptual source layout

```text
golden-path-harness/
├── AGENTS.base.md                 # provider-neutral base agent instructions
├── install.sh                     # idempotent bootstrap, if shell installer fits existing platforms
├── harness/                      # agent orchestration, policies, execution and evidence contracts
├── evaluations/                  # independent eval rules, fixtures, greenfield/brownfield cases
├── adapters/                     # provider adapters (Claude Code, Codex, others)
│   └── skills/                   # adapter-specific instructions if appropriate
├── docs/
│   ├── adr/
│   ├── proposals/
│   └── feedback/
├── infra/
│   ├── scripts/
│   ├── pipelines/
│   └── templates/
└── tests/                        # tests of the harness/tooling itself
```

Treat this as a **target taxonomy**, not a mandate to force every file into a directory. Preserve established language/package conventions and avoid redundant nesting. `evaluations/` contains test cases _for agents_, whereas `tests/` verifies _the harness_. Keep private/held-out graders inaccessible to candidate agents.

## Desired local installation

```text
~/.golden-path-harness/
  config/
  cache/
  state/
  workspaces/                 # disposable per-run directories
  logs/
  <installed harness components as needed>
```

All persistent harness-owned local directories should live under **one root**, `~/.golden-path-harness`, rather than scattering `~/harness-*` folders. Do **not** move the developer's source checkout into that directory unconditionally. Allow configurable `GOLDEN_PATH_HOME` / XDG-compatible resolution if consistent with existing conventions. Do not put secrets into generated reports or git. Avoid mixing installer-managed source and mutable runtime state. Installation should be repeatable and safe to rerun.

## Essential architectural boundaries

1. The backlog story remains authoritative for requirements and the human-approved specification. Vegviser helps prepare it; **human approval occurs before harness orchestration**.
2. The harness implements and validates that approved specification; it does not approve stories or PRs or authorize PRD releases.
3. Keep adapters replaceable and evaluation definitions provider-neutral.
4. Separate deterministic enforcement from behavioral and functional evals.
5. The implementing agent cannot alter hidden evaluators, scoring criteria, or company principles to pass its own benchmark.
6. Do not change current DEV/TEST/ACC/PRD approval rules merely because the proposed ADR favors future TEST/ACC automation. That requires policy ratification.
7. Preserve existing credentials, CLI login integration and policy boundaries. Do not invent an auth broker or require API keys without need; isolate credentials appropriately.

## Execution steps

### Step 1 — Inspect and report

- Summarize current structure, executable entrypoints, package/dependency topology, imports, configuration, tests, generated files, and automation.
- Create a mapping of existing paths to proposed destinations.
- Identify cyclic dependencies or behavior coupled to filesystem paths.
- Identify repo or pipeline constraints, and any proposed moves that would cause breakage.
- Propose the smallest incremental plan before editing.

### Step 2 — Restructure in small, reviewable changes

- Move only files with clear ownership; retain existing interfaces where practical.
- Update imports, path resolution, commands, packaging and docs together.
- Preserve backward compatibility for public entrypoints/config or provide explicit migration shims and a deprecation note.
- Keep evaluation datasets, reference projects, private graders, generated outputs, and temporary workspaces clearly distinct.
- Add `.gitignore` coverage for runtime state, credentials, cached outputs, and disposable workspaces.
- Prefer platform-independent path resolution; avoid hardcoded user directories.
- Keep installer behavior idempotent, non-destructive and testable; if a Windows-first user base exists, recommend platform-appropriate installer alternatives instead of assuming POSIX shell is universal.

### Step 3 — Verify

- Run the existing tests and add migration/path tests for moved entrypoints.
- Smoke-test adapter discovery and harness execution without paid provider calls where possible.
- Smoke-test at least one deterministic evaluator against known-good and deliberately violating fixtures.
- Validate `install.sh` in a clean temporary HOME; verify that a second run does not duplicate state or damage files.
- Verify that evaluation results are written outside protected golden fixtures.
- Produce a tree diff, list changed entrypoints and migration steps, show actual commands/results, and note anything that could not be tested.

## Output and acceptance criteria

Provide:

1. Actual before/after tree summary and file mapping.
2. A rationale for each structural change, including anything intentionally left in place.
3. Updated developer docs and run/install examples.
4. Regression results and known limitations.
5. Decisions requiring team review, especially any changes affecting approvals, credentials or public APIs.

A successful outcome preserves existing behavior, makes harness-versus-evaluation ownership unmistakable, keeps provider adapters independently replaceable, and installs without creating multiple top-level directories in the user's home directory.

**Begin with an inventory and migration plan. Do not perform broad file moves until you can substantiate the mapping from actual repository contents.**
