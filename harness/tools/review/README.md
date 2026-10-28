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
