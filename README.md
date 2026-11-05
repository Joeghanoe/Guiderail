# CodingHarness

One set of rules, examples and guardrails for every Coding repo, used the same way by Claude Code, GitHub Copilot and the PR pipeline. It answers one question:

> Was this change checked against our standards, and can we show which standards and what they found?

This repo is the single source of truth. Nothing is copied into project repos: developers install it once ([install.sh](install.sh)), and the PR pipeline checks it out at a pinned commit and removes it again after the run.

The knowledge is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle: Markdown with frontmatter and an [index.md](harness/index.md) per folder. Agents start at the index and open only what a change touches, rather than loading every instruction file up front.

Material changes and approval outcomes are summarized in [harness/log.md](harness/log.md). Current conventions live in [docs/decisions/feedback-conventions.md](docs/decisions/feedback-conventions.md); architectural decisions remain in `docs/adr/`.

Executable check usage lives with the [verification tools](harness/tools/verification/index.md). Audits, model comparisons and verification run reports belong in `$GOLDEN_PATH_HOME/testing/`, defaulting to `~/.golden-path-harness/testing/`, outside Git.

The [unified CLI](harness/tools/cli/index.md) provides change review, Azure DevOps run diagnosis/watching, frontend capture/comparison, greenfield initialization, and native skill-selection evaluation. [install.sh](install.sh) installs `tvh` under `$GOLDEN_PATH_HOME/bin` and the automatically selected review skill for Claude Code and Copilot. Pipeline diagnosis stays a playbook and CLI operation. Add the executable directory to PATH or invoke it directly. The CLI and skill ship with the harness revision. All current public tool operations have CLI routes; `tvh tools --check --json` verifies coverage. Private libraries, provider adapters and direct CI implementation calls remain internal.

```bash
./harness/tvh doctor --json
./harness/tvh context select --repo . --changed --baseline HEAD --brief
./harness/tvh verify --repo . --json
./harness/tvh review --repo . --baseline origin/main --engine copilot --json
```

## Layers

| Layer | What | Hard or soft |
| --- | --- | --- |
| 1. Identity | Agents use a read-only cloud login; the review job has no service connection | **Hard**: the real boundary |
| 2. Tools | `scripts/verify.sh`, [cloud-read.sh](harness/tools/cloud/cloud-read.sh), [check-scenarios.py](harness/tools/testing/check-scenarios.py), analyzers (optional [BannedSymbols.txt](harness/templates/repo/BannedSymbols.txt)) | Hard for what goes through them |
| 3. Hooks and settings | Claude Code `PreToolUse` guards, the `Stop` verify, permission deny rules | Guardrail |
| 4. Instructions | [AGENTS.base.md](AGENTS.base.md), rules, examples | Soft |

If layer 1 is wrong, the rest only looks safe.

Local agent processes should not inherit shell variables containing credentials. The Bash hook blocks common environment-dump commands, including Python, Node.js and PowerShell forms, but it is a guardrail rather than a security boundary. Prefer starting the editor/agent from a shell without sensitive variables.

## Layout

```text
AGENTS.base.md        the base instructions every agent loads
harness/              the bundle (~/.golden-path-harness/harness after install.sh)
  index.md            the entry point
  log.md              dated summaries of material changes; Git holds the authoritative history
  principles/         P1-P13: pointers to Vegviser, which is the authority
  rules/              security, cloud, iac, delivery, testing, harness: each says what enforces it
  examples/           worked examples with good and bad code; human-reviewed ones are precedent and the reviewer eval instrument
  gates/              registration of each deterministic check (tool, owner, coverage, blind spots)
  playbooks/          review a change, add an example, process feedback, classify a test failure, write a business test plan,
                      write a spec, scaffold from a repo's conventions, optimize build duration, compress harness prose
  templates/          example.md, finding.md, spec.md, solution-design.md, project-terms.txt, business-testplan.spec.json;
                      repo/ has the project-owned AGENTS.md and scripts/verify.sh;
                      scenario mapping and BannedSymbols/analyzer files are opt-in, not scaffolded requirements
  tools/              grouped by domain, see tools/index.md: harness/, review/, testing/, cloud/, azure-devops/, servicenow/,
                      sonar/, frontend/, deps/, dev/, spec/, scaffold/, orchestration/
  hooks/              guard-bash.sh, guard-read.sh, stop-verify.sh
feedback/             draft examples from every repo (~/.golden-path-harness/feedback), reviewed weekly
skills/               engineering process skills, installed by install.sh
benchmarks/          agent evaluation scenarios (task, criteria, run profiles); tests/ verifies the harness itself
infra/scripts/        CI and local helper scripts (context budget, review-changed, eval-home-setup)
infra/pipelines/ai-review.yml   Azure DevOps steps template: pin, verify, T.5, AI review, receipt, clean-up
install.sh            installs the harness for your user; removes the old AI Hub wiring
tests/run.sh          tests for the tools, hooks and install; no network
```

## Local testing records

Use `~/.golden-path-harness/testing/` for audit documents, experiment scripts, comparison reports, generated workspaces and raw run evidence. Use `archives/` for frozen report snapshots and `runs/` for execution artifacts. Keep credentials out of both. Installation and uninstall preserve this directory.

Reusable checks, deterministic test fixtures and benchmark task definitions remain versioned with their code. One-off findings and machine-specific run results do not belong in the checkout.

The [reference project validation workflow](benchmarks/reference-projects.md) explains how to register existing projects under the local testing directory, pin their sources and record expected improvements for repeatable harness evaluations.

## Install (once per machine)

```bash
./install.sh          # again after every git pull; ./install.sh --uninstall undoes it
```

- creates the one harness root `~/.golden-path-harness` (or `$GOLDEN_PATH_HOME`) with `harness/` and `feedback/` links plus `config/ cache/ state/ workspaces/ logs/ testing/` for runtime state, which update and uninstall never delete;
- removes the old top-level `~/.harness` and `~/.harness-feedback` links if present (run it once after pulling this change; the hooks and allow rules in `~/.claude/settings.json` are rewritten to the new root);
- imports [AGENTS.base.md](AGENTS.base.md) from `~/.claude/CLAUDE.md`;
- adds the guard hooks and the Stop verify for Claude Code;
- installs complete engineering skill packages, including `code-review`, in `~/.claude/skills/` and `~/.copilot/skills/` for automatic selection or explicit invocation; pipeline diagnosis uses shared playbooks and CLI commands within debugging;
- installs `tvh` in `$GOLDEN_PATH_HOME/bin` without editing shell profiles or granting broad command permissions;
- adds the instructions for Copilot in VS Code;
- removes the old AI Hub import, marketplace and `Bash(az ...)` allow rules.

Every changed file is backed up first.

After installing, start a fresh Copilot chat and check `/code-review` in the slash menu. In VS Code, `Chat: Open Customizations` > Skills shows discovered skills. Existing VS Code profiles may also show a `Review Migrations` notice for older customizations; review those separately. Installing general instructions alone does not register `/code-review`.

Give agents a read-only cloud login, once per machine. You run this, never an agent:

```bash
export HARNESS_AZURE_CONFIG_DIR="$HOME/.azure-reader"     # in your shell profile
AZURE_CONFIG_DIR="$HOME/.azure-reader" az login             # with an account that only has Reader
```

No separate reader account? Skip the export: after your own `az login`, [cloud-read.sh](harness/tools/cloud/cloud-read.sh) reads with that login and only its read-verb and secret checks limit it (E-015). Each fallback invocation warns on stderr, and `az rest` is blocked unless an explicit `HARNESS_AZURE_CONFIG_DIR` is configured. Not logged in means the read fails; you log in.

Tool secrets (the Sonar token for [sonar-read.sh](harness/tools/sonar/sonar-read.sh), the ServiceNow account for [sn-get.sh](harness/tools/servicenow/sn-get.sh)) go in `~/.config/harness/.env`, outside every repo; start from `harness/.env.example`. Agents read the example, never the file; the wrappers read the file themselves.

Requirements: bash, jq, python3 and git. On Windows, Claude Code runs hooks through Git Bash.

## What a project repo owns

Only what is specific to the repo:

- `AGENTS.md`: the repo's own instructions, including its naming convention (IAC.6). Claude Code, Copilot and Codex read it natively. Start from `AGENTS.md`.
- `scripts/verify.sh`: the repo's format, analyzer, build and test steps; `--fast` for the Stop hook.
- Optional: `.harness-scenarios.json` (components and their scenario folders, T.5), and for .NET `Directory.Build.props` with [BannedSymbols.txt](harness/templates/repo/BannedSymbols.txt) (the T.2 build gate; copy them from `harness/templates/repo/`).
- The PR pipeline: add [ai-review.yml](infra/pipelines/ai-review.yml) as a template; see its header. Pin a tag and pass its commit SHA as `harnessCommit`; a tag can move, the SHA cannot. The run links the checkout as `.harness/` and removes it at the end, also after a failure.

Copilot code review on GitHub runs on GitHub's servers and cannot see [harness](harness); for a GitHub repo, the review runs through the pipeline instead.

## Is it loaded? (adapter check)

An `@import` that is present is not proof that it was expanded. `tvh context check-adapter --raw -- [dir]` asks the agent, without tools, whether the marker `tvh-loaded` is in its instructions. That costs one short prompt.

| Tool | Where | Result | Date |
| --- | --- | --- | --- |
| Claude Code 2.1.302 | a folder without repo config (global install) | loaded | 2026-10-18 |
| Copilot (VS Code) | a folder without repo config (global install) | not verified yet |  |

Re-run after a Claude Code or Copilot update, or a change to how the adapter imports.

## Evaluate the reviewer

Reviews use explicit adversarial topics: spec coverage, access and least privilege, failure and recovery, operations and capacity, and delivery risks. Pass additional topics to `/code-review` with the target. A repository or release review follows [review-repository.md](skills/engineering/code-review/REVIEW-REPOSITORY.md); change reviews keep the existing fix workflow. The [human report template](harness/templates/review-report.md) records scope, checks, decisions, spec coverage, findings and open verifications. Pipeline findings retain their existing JSON contract.

The AI review is only trusted as far as its evals show (Vegviser AI Evaluation Standard). Human-verified violation, compliant and boundary examples generate reviewer evals; undecided feedback and automation proposals do not. Their bad examples must be flagged by the linked rule and their good examples must not; boundary cases test only the good side. Run `tvh eval reviewer --raw --` after changing rules, examples, playbooks or the review tools; CI does the same. Engines, gate thresholds, evidence and options: [harness/tools/review/README.md](harness/tools/review/README.md). The [verdict and status reference](docs/example-verdicts.md) explains classification, human acceptance, advisory cases and pass/fail/error results.

## How the harness learns

- **Feedback, in one place.** A correction of harness output, from any repo, becomes a draft example in [feedback](feedback) (this repo's `feedback/`). A human reviews the drafts, moves the accepted ones into `harness/examples/` with `verified`, and commits. Principles are Vegviser's; the harness only points to P1-P13 (rule H.1).
- **Trust.** An example with `verified: { by: human:<id>, ... }` is precedent for the reviewer and an eval; an unverified example is a hint.
- **PR threads.** The reviewer posts each finding as a thread. Its resolution (Fixed, Won't fix, By design) is the feedback signal.
- **Automation ladder.** A repeated task becomes a playbook, then a script, then a hook or CI check (rule H.2).

## Change the harness

Install the Markdown commit hook once per clone:

```bash
pipx install pre-commit==4.7.0    # or: uv tool install pre-commit==4.7.0
pre-commit install
```

The hook runs a pinned Prettier version on staged Markdown files. It removes extra blank lines, keeps each prose paragraph on one source line, and leaves code fences unchanged. If it reformats a file, review the changes, stage them again and retry the commit. Pre-commit keeps unstaged edits out of the hook run.

Run `pre-commit run --all-files` to format existing Markdown. CI runs the same check and fails if formatting changes are needed. Generated concept indexes are excluded because [bundle.py](harness/tools/harness/bundle.py) owns their exact contents.

```bash
tvh bundle index --raw --    # after adding or renaming a concept
tvh bundle check --raw --    # OKF conformance, IDs, links, code in examples, indexes
tvh bundle privacy-check --raw --
tvh bundle budget --raw --       # always-loaded text (AGENTS.base.md, index.md) stays within its recorded size
tests/run.sh                             # tools, hooks and install
tvh eval reviewer --raw --  # the reviewer, when rules, examples or the review changed
```

Git history is the change log; write the why in the commit message. CI ([azure-pipelines.yml](azure-pipelines.yml)) runs the same checks plus shellcheck, and the evals when the review changed.

## Model-agnostic

The harness does not assume a vendor. Rules, playbooks and tools speak in tiers (`economy`, `builder`, `reasoner`); a model name is a lookup that differs per platform and goes stale. [models.json](harness/tools/orchestration/models.json) holds the names the harness can vouch for, `~/.config/harness/models.json` adds yours, and no provider is the default ([details](harness/tools/orchestration/index.md)). The review runs on Claude Code, Copilot or Agy (`HARNESS_REVIEW_ENGINE`); Claude is today's default engine, not a requirement.

## Not built yet

- Trigger and non-trigger evals for `/code-review`, and precision per rule over many PRs.
- A scheduled job that collects resolved PR threads into draft examples.
- A GitHub Actions variant of [ai-review.yml](infra/pipelines/ai-review.yml).
- A deterministic attester for the review receipt (`receipt.json` is published as an artifact today).

Engineering process entry points, ownership and planned coverage are in the [process catalog](skills/index.md).

The accepted [architecture decisions](docs/adr/index.md) record the CLI and process-skill contracts.
