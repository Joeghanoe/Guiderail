---
name: verification
description: TeamValue definition-of-done gate — always format, resolve or mark new lint issues, and run build and tests before calling work complete.
---

You are finishing a code change. Before reporting work as done, run this verification gate. These steps are mandatory whenever the relevant command is available, not optional polish. Applies to all languages; for TypeScript specifics see [[typescript]], for review depth see [[frontend-security]].

## Use the project's own toolchain

- Detect what the project uses and run *that* — never assume a default runner.
- Pick the package manager from the lockfile: `bun.lockb`/`bun.lock` → `bun`, `pnpm-lock.yaml` → `pnpm`, `yarn.lock` → `yarn`, `package-lock.json` → `npm`. For other ecosystems use their native tool (`dotnet`, `cargo`, `go`, `mvn`/`gradle`, `uv`/`poetry`/`pip`, etc.).
- Run scripts through that manager (`bun run <script>`, `pnpm <script>`, `yarn <script>`, `npm run <script>`).
- If signals conflict or none is present, match what the repo docs or existing CI use; if still unclear, ask rather than guessing.

## Formatting

- If a format command is available, **always run it** before finishing, invoked through the project's toolchain (e.g. `bun run format`, `pnpm format`, `dotnet format`).
- Discover the command from the project (scripts in `package.json`, a `Makefile`, repo docs) rather than assuming one.
- Never hand-format to fight the formatter; run the tool and accept its output.
- If no format command exists, match the surrounding file's existing style.

## Linting

- If a lint command is available, **always run it** and address every issue your change newly introduced.
- Resolve new issues by fixing the code — not by relaxing the rule.
- If an issue genuinely must be suppressed, **mark it explicitly**: a scoped, inline ignore (e.g. `// eslint-disable-next-line <rule>`) with a short reason comment. No blanket file-level or repo-level disables to pass.
- Pre-existing, unrelated lint issues are out of scope — do not silence them and do not let them mask new ones. Note them if they block.

## SonarQube (if installed)

- If the project uses SonarQube — a SonarLint / SonarQube for IDE extension, a `sonar-project.properties`, or a `sonar-scanner` CLI — **run analysis on the change** before finishing.
- Scope it to the **staged files on the current branch**, not the whole tree: analyze the staged diff (e.g. `git diff --cached --name-only`) so findings map to your change.
- Treat new findings the same as lint: fix them, or if one must stand, mark it with a scoped, justified suppression (e.g. a `// NOSONAR <reason>` or rule-level exclusion) — never a blanket project disable.
- Honour the project's quality gate. Do not lower thresholds or exclude files to pass.
- If SonarQube is not installed/configured, skip this step and say so — do not install or configure it unprompted.

## Build and tests

- **Always run the build** and confirm the change compiles cleanly. Treat warnings introduced by your change as failures to address.
- **Always run the tests** relevant to the change (the full suite when fast enough, otherwise the affected scope).
- Verify the result against the spec — the goal is "does what it should," not just "compiles and is green."
- If you add behavior, add or update tests for it. If tests are owned elsewhere, leave the code testable and say so.

## Reporting honestly

- Report outcomes faithfully. If the build or tests fail, say so and show the output — do not claim done.
- If you skipped a step (no command available, suite too slow, environment missing), state which step and why.
- Only call work complete after format, lint, SonarQube (when present), build, and tests have actually been run and pass — or you have named exactly what was skipped.

## Anti-patterns (avoid)

- Declaring work "done" without running build or tests.
- Suppressing lint errors wholesale to get a clean run.
- Hand-formatting instead of running the formatter.
- Silencing pre-existing failures to make your change look green.
- Lowering the SonarQube quality gate or excluding files to pass it.
- Claiming green without having run the commands.

## Review checks

- Was the format command run (or its absence stated)?
- Were all newly introduced lint issues fixed, or each suppression scoped and justified?
- If SonarQube is present, was it run on the staged files and its findings resolved or justified?
- Does the build compile cleanly, with no new warnings?
- Were the relevant tests run and do they pass?
- Does the behavior match the spec, not just the type checker?
- Was any skipped step named explicitly rather than glossed over?
