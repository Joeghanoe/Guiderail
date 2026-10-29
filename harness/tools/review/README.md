# Evaluating the reviewer

The AI review is only trusted as far as its evals show (Vegviser AI Evaluation Standard).
`harness/tools/review/eval.py` builds a throwaway repo for each case, reviews it with `review.sh` (the same
script the PR pipeline runs), and scores the findings without an LLM. Run with the default Claude CLI or
`--engine copilot` to use the GitHub Copilot CLI.

- **Cases are the examples and the evals.** Every human-verified case adds scenarios: its bad example must
  be flagged by its rule, its good example must not (a `boundary` case only checks its good side). Accepting
  a case extends the regression set; there is one place to write an example. Each tested violation/compliance
  case is removed from the throwaway review bundle, preventing the evaluator from teaching the reviewer the
  exact code it is testing. `boundary` cases stay visible because their precedent is the behavior under test.
- **Reviewer behavior** is expressed as optional sections and `eval_behavior` metadata on the same Markdown
  cases: `adversarial` supplies untrusted PR text, while `rename` creates a before/after file rename.
- **Drafts are advisory:** unverified cases (other than `eval_behavior` cases) are evaluated in the same run but
  never count toward the gate. Their results print and are recorded under `summary.advisory`, so a draft that
  the reviewer gets wrong is visible without blocking. Verifying the case makes it gate.
- **Gate:** `harness/tools/review/thresholds.json`. Every critical scenario (security, adversarial, abstention) passes all of
  its repeats, because the reviewer is not deterministic; the overall pass rate meets the minimum.
- **Evidence:** local results are written outside the checkout under the system temporary directory; CI publishes
  them as an artifact. A full run on a clean commit appends one summary line to
  `harness/tools/review/history.jsonl`; raw failed output is not committed.
- **When:** harness CI runs the evals when rules, playbooks, cases, templates, or review/evaluation tools change.
  The evaluator masks the case being tested, except for a boundary case whose precedent is the subject of the test.

```bash
python3 -I harness/tools/review/eval.py                       # all eligible cases, Claude engine
python3 -I harness/tools/review/eval.py --engine copilot      # all eligible cases, GitHub Copilot CLI
python3 -I harness/tools/review/eval.py --engine copilot --jobs 4
python3 -I harness/tools/review/eval.py --only case-c-018-pr-description-cannot-waive-a-rule-bad
```

The Claude engine requires an authenticated Claude CLI. Check with `claude auth status`; if logged out, run
`claude` and enter `/login`. The Copilot engine requires the GitHub Copilot CLI (`copilot login` to authenticate).
Both engines restrict the reviewer to read-only tools. The evaluator runs up to two scenarios concurrently by
default (`--jobs` accepts 1-8) and prints a flushed result line as each eval run completes. The evaluator checks
CLI availability before creating scenarios, so a missing CLI does not get recorded as failed review results.

The reviewer is limited to 10 turns and a 180-second wall-clock timeout. `bundle.py privacy-check` makes CI
fail if private mined comments or raw eval artifacts are present in the checkout.

# One scenario at a time, with a checklist

`eval.py` is all or nothing, and a run that dies halfway (model quota, login expiry) loses its finished work and
records the dead runs as a bad reviewer. `eval-queue.py` runs the same scenarios, with the same scoring (it imports
`eval.py`), one at a time, and writes a checklist after each. Run it again and it carries on.

```bash
python3 -I harness/tools/review/eval-queue.py status                  # what is checked, what is left, what it costs
python3 -I harness/tools/review/eval-queue.py run --limit 3           # three scenarios, then stop; spread tokens over days
python3 -I harness/tools/review/eval-queue.py run                     # everything left, Copilot by default
python3 -I harness/tools/review/eval-queue.py run --engine claude --no-advisory
```

- **Three outcomes.** `pass` and `fail` are results and get checked off. `error` (quota, login, timeout, CLI gone) is
  not a result: it stays unchecked and is retried, so running out of tokens never becomes "the reviewer failed".
  A `fail` is not re-run unless you pass `--retry-failed`.
- **It stops instead of grinding.** A quota or login error stops the run at once and says so. Before any scenario
  has worked, the first error stops it too: after the 0.0 run in `history.jsonl`, a broken setup should cost one
  review, not forty. Once something has worked, `--max-errors` (default 2) in a row stops it.
- **Cheapest first.** One cheap gating scenario goes first as a smoke test, then the critical ones (three reviews
  each), then the rest, then the drafts. `--no-advisory` skips the drafts, which cannot fail the gate.
- **The checklist** is `checklist.md` (readable, with `[x]` pass, `[!]` fail, `[?]` could not run) and
  `checklist.json`, under `~/.harness-evals/<engine>-<model>-<bundle hash>/`, outside every repo. It belongs to one
  engine, one model and one state of the rules, cases, playbooks, templates and review tools; change any and a fresh
  one starts, and the old one is kept but not used.
- **The verdict** is `eval.py`'s gate line, printed once every gating scenario has a result. Exit 0 finished and
  passing, 1 finished and failing, 2 usage or the engine is unusable, 3 stopped early (resume with the same command).
- **History.** `--append-history` records the run in `history.jsonl` as `eval.py` does, only for a complete run on a
  clean commit.

It cannot know your quota. It recognises the usual wording of a quota or login failure; for any other wording it
relies on the consecutive-error stop, and always prints the engine's message.

## Where results live, and what is known (2026-10-29)

- The checklist is local, not in the repo: `~/.harness-evals/<engine>-<model>-<bundle hash>/checklist.md` (and
  `checklist.json`). The hash changes when the rules or cases change, which starts a fresh checklist.
  `eval-queue.py status` prints its path. Only a complete run on a clean commit is appended to `history.jsonl`
  (`--append-history`); partial progress stays in the checklist.
- Progress so far (engine `claude`, default model, bundle `3aa41de24d`): 1 of 44 scenarios checked, 1 pass
  (`case-c-001-services-get-their-http-client-injected-bad`). 43 left, about 49 reviews.
- `--engine copilot` on Windows: Copilot CLI 1.0.51 (WinGet) failed with `unknown option '--no-warnings'` when
  launched by `run-copilot.py` (restricted environment); run directly it answered `402 You have exceeded your
  monthly quota`. The cause of the first error is not found; it is not in this repo. Use `--engine claude` until fixed.
- The flag is `--limit`, not `--run-limit`.
