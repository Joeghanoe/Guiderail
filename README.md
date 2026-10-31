# CodingHarness

One set of rules, examples and guardrails for every Coding repo, used the same way by Claude Code,
GitHub Copilot and the PR pipeline. It answers one question:

> Was this change checked against our standards, and can we show which standards and what they found?

This repo is the single source of truth. Nothing is copied into project repos: developers install it once
(`install.sh`), and the PR pipeline checks it out at a pinned commit and removes it again after the run.

The knowledge is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle: Markdown with frontmatter and an `index.md` per folder. Agents start at the index and open only what a
change touches, rather than loading every instruction file up front.

## Layers

| Layer | What | Hard or soft |
|---|---|---|
| 1. Identity | Agents use a read-only cloud login; the review job has no service connection | **Hard**: the real boundary |
| 2. Tools | `scripts/verify.sh`, `cloud-read.sh`, `check-scenarios.py`, analyzers (optional `BannedSymbols.txt`) | Hard for what goes through them |
| 3. Hooks and settings | Claude Code `PreToolUse` guards, the `Stop` verify, permission deny rules | Guardrail |
| 4. Instructions | `AGENTS.base.md`, rules, examples | Soft |

If layer 1 is wrong, the rest only looks safe.

Local agent processes should not inherit shell variables containing credentials. The Bash hook blocks common
environment-dump commands, including Python, Node.js and PowerShell forms, but it is a guardrail rather than
a security boundary. Prefer starting the editor/agent from a shell without sensitive variables.

## Layout

```text
AGENTS.base.md        the base instructions every agent loads
harness/              the bundle (~/.golden-path-harness/harness after install.sh)
  index.md            the entry point; git history is the change log
  principles/         P1-P13: pointers to Vegviser, which is the authority
  rules/              security, cloud, iac, delivery, testing, harness: each says what enforces it
  examples/           worked examples with good and bad code; human-reviewed ones are precedent and the reviewer eval instrument
  gates/              registration of each deterministic check (tool, owner, coverage, blind spots)
  playbooks/          review a change, add an example, process feedback, classify a test failure, write a business test plan,
                      write a spec, scaffold from a repo's conventions, optimize build duration, compress harness prose
  templates/          example.md, finding.md, spec.md, solution-design.md, project-terms.txt, business-testplan.spec.json;
                      repo/ is what a project repo owns itself: AGENTS.md, scripts/verify.sh, .harness-scenarios.json;
                      Directory.Build.props and BannedSymbols.txt are optional (T.2 build gate)
  tools/              grouped by domain, see tools/index.md: harness/, review/, testing/, cloud/, azure-devops/, servicenow/,
                      sonar/, frontend/, deps/, dev/, spec/, scaffold/, orchestration/
  hooks/              guard-bash.sh, guard-read.sh, stop-verify.sh
feedback/             draft examples from every repo (~/.golden-path-harness/feedback), reviewed weekly
adapters/             /tv-review for Claude Code, installed by install.sh
benchmarks/          agent evaluation scenarios (task, criteria, run profiles); tests/ verifies the harness itself
infra/scripts/        CI and local helper scripts (context budget, review-changed, eval-home-setup)
infra/pipelines/ai-review.yml   Azure DevOps steps template: pin, verify, T.5, AI review, receipt, clean-up
install.sh            installs the harness for your user; removes the old AI Hub wiring
tests/run.sh          tests for the tools, hooks and install; no network
```

## Install (once per machine)

```bash
./install.sh          # again after every git pull; ./install.sh --uninstall undoes it
```

- creates the one harness root `~/.golden-path-harness` (or `$GOLDEN_PATH_HOME`) with `harness/` and `feedback/` links plus `config/ cache/ state/ workspaces/ logs/` for runtime state, which update and uninstall never delete;
- removes the old top-level `~/.harness` and `~/.harness-feedback` links if present (run it once after pulling this change; the hooks and allow rules in `~/.claude/settings.json` are rewritten to the new root);
- imports `AGENTS.base.md` from `~/.claude/CLAUDE.md`;
- adds the guard hooks, the Stop verify and `/tv-review` for Claude Code;
- adds the instructions for Copilot in VS Code;
- removes the old AI Hub import, marketplace and `Bash(az ...)` allow rules.

Every changed file is backed up first.

Give agents a read-only cloud login, once per machine. You run this, never an agent:

```bash
export HARNESS_AZURE_CONFIG_DIR="$HOME/.azure-reader"     # in your shell profile
AZURE_CONFIG_DIR="$HOME/.azure-reader" az login             # with an account that only has Reader
```

No separate reader account? Skip the export: after your own `az login`, `cloud-read.sh` reads with that login
and only its read-verb and secret checks limit it (E-015). Each fallback invocation warns on stderr, and `az rest`
is blocked unless an explicit `HARNESS_AZURE_CONFIG_DIR` is configured. Not logged in means the read fails; you log in.

Tool secrets (the Sonar token for `sonar-read.sh`, the ServiceNow account for `sn-get.sh`) go in `~/.config/harness/.env`, outside every repo; start from
`harness/.env.example`. Agents read the example, never the file; the wrappers read the file themselves.

Requirements: bash, jq, python3 and git. On Windows, Claude Code runs hooks through Git Bash.

## What a project repo owns

Only what is specific to the repo:

- `AGENTS.md`: the repo's own instructions, including its naming convention (IAC.6). Claude Code, Copilot and
  Codex read it natively. Start from `harness/templates/repo/AGENTS.md`.
- `scripts/verify.sh`: the repo's format, analyzer, build and test steps; `--fast` for the Stop hook.
- Optional: `.harness-scenarios.json` (components and their scenario folders, T.5), and for .NET
  `Directory.Build.props` with `BannedSymbols.txt` (the T.2 build gate; copy them from `harness/templates/repo/`).
- The PR pipeline: add `infra/pipelines/ai-review.yml` as a template; see its header. Pin a tag and pass its commit
  SHA as `harnessCommit`; a tag can move, the SHA cannot. The run links the checkout as `.harness/` and
  removes it at the end, also after a failure.

Copilot code review on GitHub runs on GitHub's servers and cannot see `~/.golden-path-harness/harness`; for a GitHub repo, the
review runs through the pipeline instead.

## Is it loaded? (adapter check)

An `@import` that is present is not proof that it was expanded. `tools/harness/check-adapter.sh [dir]` asks the
agent, without tools, whether the marker `tvh-loaded` is in its instructions. That costs one short prompt.

| Tool | Where | Result | Date |
|---|---|---|---|
| Claude Code 2.1.302 | a folder without repo config (global install) | loaded | 2026-10-18 |
| Copilot (VS Code) | a folder without repo config (global install) | not verified yet | |

Re-run after a Claude Code or Copilot update, or a change to how the adapter imports.

## Evaluate the reviewer

The AI review is only trusted as far as its evals show (Vegviser AI Evaluation Standard). Every human-verified
example is also an eval: its bad example must be flagged by its rule, its good example must not. Run
`python3 -I harness/tools/review/eval.py` after changing rules, examples, playbooks or the review tools; CI does
the same. Engines, gate thresholds, evidence and options: [harness/tools/review/README.md](harness/tools/review/README.md).

## How the harness learns

- **Feedback, in one place.** A correction of harness output, from any repo, becomes a draft example in
  `~/.golden-path-harness/feedback/` (this repo's `feedback/`). A human reviews the drafts, moves the accepted ones into
  `harness/examples/` with `verified`, and commits. Principles are Vegviser's; the harness only points to P1-P13
  (rule H.1).
- **Trust.** An example with `verified: { by: human:<id>, ... }` is precedent for the reviewer and an eval; an
  unverified example is a hint.
- **PR threads.** The reviewer posts each finding as a thread. Its resolution (Fixed, Won't fix, By design) is
  the feedback signal.
- **Automation ladder.** A repeated task becomes a playbook, then a script, then a hook or CI check (rule H.2).

## Change the harness

```bash
python3 harness/tools/harness/bundle.py index    # after adding or renaming a concept
python3 harness/tools/harness/bundle.py check    # OKF conformance, IDs, links, code in examples, indexes
python3 harness/tools/harness/bundle.py privacy-check
python3 harness/tools/harness/bundle.py budget       # always-loaded text (AGENTS.base.md, index.md) stays within its recorded size
tests/run.sh                             # tools, hooks and install
python3 -I harness/tools/review/eval.py  # the reviewer, when rules, examples or the review changed
```

Git history is the change log; write the why in the commit message. CI (`azure-pipelines.yml`) runs the same
checks plus shellcheck, and the evals when the review changed.

## Model-agnostic

The harness does not assume a vendor. Rules, playbooks and tools speak in tiers (`economy`, `builder`, `reasoner`);
a model name is a lookup that differs per platform and goes stale. `tools/orchestration/models.json` holds the names
the harness can vouch for, `~/.config/harness/models.json` adds yours, and no provider is the default
([details](harness/tools/orchestration/index.md)). The review runs on Claude Code, Copilot or Agy
(`HARNESS_REVIEW_ENGINE`); Claude is today's default engine, not a requirement.

## Not built yet

- Trigger and non-trigger evals for `/tv-review`, and precision per rule over many PRs.
- A scheduled job that collects resolved PR threads into draft examples.
- A GitHub Actions variant of `infra/pipelines/ai-review.yml`.
- A deterministic attester for the review receipt (`receipt.json` is published as an artifact today).
