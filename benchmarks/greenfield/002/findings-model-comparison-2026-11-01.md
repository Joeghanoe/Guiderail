# greenfield-002: Codex (gpt-6.1 terra and sol) against Claude Sonnet 5.5

Runs on 2026-11-01, container isolation, one frozen package (`greenfield-002-terra1`, manifest sha256 `9a69b1dda598f4833ee13597c9097f5f219fb4c26742d056830d3e58d0c9e0d1`), harness commit cd69482. Grader for every run: `claude -p --model claude-opus-5-5`. All runs are class `isolated-container`; overall status is `inconclusive` for all of them because policy and behavior need trace review. Evidence lives outside the repo in `~/.harness-evaluation/runs/greenfield-002-<name>/`.

## Conclusion

Sol and Sonnet 5.5 pass every measured dimension, including the design gate (D01-D09). Terra passes functional, build and tests but fails the design gate in all three samples (D05-D09 every time). Terra is about 20 times faster than sol because it skips the design, DI and test-layering work. Sol is about 4.7 times slower than Sonnet for the same result.

## Results

| Run | Model | Time | Functional | CODE.5 | Design failures | Tokens in / out | Tool calls | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| terra2 | gpt-6.1-terra | 95 s | pass | fail (1 finding) | D04-D09 | 368k / 7.5k | 14 | n/a |
| terra3 | gpt-6.1-terra | 61 s | pass | pass | D01-D09 (no design doc, ADRs or repo AGENTS.md) | 136k / 5.5k | 6 | n/a |
| terra4 | gpt-6.1-terra | 103 s | pass | pass | D05-D09 | 406k / 8.4k | 21 | n/a |
| sol1 | gpt-6.1-sol | 2157 s | pass | pass | none | 3.09M / 78k | 42 | n/a |
| sonnet1 | claude-sonnet-5-5 | 456 s | pass | pass | none | 2.06M / 72k | 113 | $1.35 |

`terra1` is excluded: the Codex sandbox failed before the agent read `TASK.md` (13 s, 2 tool calls), so it measures nothing.

## What the failures look like

- Terra builds a working monolith: no DI registrations (D05), no interfaces or implementations (D06, D07), no error-code catalogue (D08), no tests that reach the component through the entry point (D09). Its own final message says the service "remains monolithic".
- Terra skips design-first in 1 of 3 samples (terra3). In terra2 `scripts/verify.sh` failed D04.
- Sol and Sonnet both wrote the design, ADRs and repo `AGENTS.md`, then built to them. Sol reports 71 tests.
- Terra's failures follow the model's shortcuts, not the harness: the same instructions produced a pass in sol, so rule delivery to Codex (`AGENTS.md`) is not the cause. Not yet tested: whether stronger wording moves terra.

## Caveats

- One sample for sol and sonnet, three for terra; rubric and design verdicts are LLM-judged. Treat as a pattern, not a score (ADR 0005).
- Sol and sonnet ran partly in parallel, which may have inflated both wall-clock times slightly.
- Codex ran with `--sandbox danger-full-access`, Claude with its own default permission mode, so tool-level isolation differs; both ran inside the same container boundary.
- Codex reports tokens, not cost, so cost cannot be compared.
- `diagnose_run.py propose` returned 0 doubtful results for terra2, so there is no `diagnosis.json`; the failed checks are clear model behaviour, not evaluator doubt.

## Running this again

1. Freeze from a clean tree (examples are excluded from the candidate, so dirty examples do not matter): `python3 harness/tools/testing/run_candidate.py freeze --scenario benchmarks/greenfield/002/scenario.json --approval "<who asked, when>" --out ~/.harness-evaluation/frozen/<name>` Keep the printed `manifest_sha256`.
2. Profile: copy a `run-profile.*.container.json` from this directory to `~/.harness-evaluation/profiles/`. For another Codex model, change the model name in `options` and in the adapter `--model`; available slugs are in `~/.codex/models_cache.json` (this run used `gpt-6.1-terra` and `gpt-6.1-sol`). Add the Opus grader (see `bf-codex-terra.json`) so grading stays comparable.
3. Codex login, once per volume. The adapter's own `login` command uses a port-forwarded browser callback that fails (`ERR_EMPTY_RESPONSE`, the container login server listens on its own localhost). Use device auth instead, and remove any leftover `eval-login` container first:
   ```
   docker rm -f eval-login
   docker run --rm -it --name eval-login --cap-drop ALL --security-opt no-new-privileges -e HOME=/home/agent -v harness-eval-home:/home/agent harness-eval:local codex login --device-auth
   ```
   Check `.codex/auth.json` exists in the volume afterwards. Login is always done by a person (CLD.1).
4. The Codex profile must pass `--sandbox danger-full-access`. With the default `workspace-write`, Codex cannot create a sandbox namespace inside the container and stops without reading the task (that was `terra1`). The container is the boundary.
5. Run: `python3 harness/tools/testing/run_candidate.py run --frozen <frozen dir> --manifest-sha256 <sha> --profile <profile> --out ~/.harness-evaluation/runs/<name>`. Two runs can go in parallel, but expect longer wall-clock times. Sol needs about 40 minutes of the 60 minute budget.
6. Read `report.md`, then `logs/design.json` for the failed D-checks and `trace/codex-last-message.txt` for the agent's own account.

## Open items

- A second sol sample to check consistency (about 36 minutes).
- Whether terra passes the design gate with stronger greenfield wording in `AGENTS.md`; the hypothesis is a model gap, not a delivery gap.
- Review the sol and sonnet traces for behavior (truthfulness, workflow) so the `inconclusive` can be resolved.
