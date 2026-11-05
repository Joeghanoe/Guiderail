# Unified harness CLI

`tvh` is the supported invocation interface for every current public harness tool. The [command catalog](commands.md) lists all routes and the internal implementations deliberately kept private. Run `tvh tools --check --json` to verify that every executable tool file is classified. The review skill selects its canonical process. Operational tasks use playbooks and commands directly; pipeline diagnosis has no dedicated skill.

From a checkout, run `./harness/tvh`. After [install.sh](../../../install.sh), add `~/.golden-path-harness/bin` to PATH or use its `tvh` executable directly. `GOLDEN_PATH_HOME` relocates the installed executable and skill references. The installer never edits shell profiles or adds a blanket `tvh` permission rule. A conflicting executable in the installation directory is refused; a different executable already on PATH is reported.

```bash
tvh doctor --json
tvh context select --repo . --changed --baseline HEAD --brief
tvh context select --repo . src/Orders.cs
tvh verify --repo . --json
tvh review --repo . --baseline origin/main --engine copilot --json
tvh ado run diagnose --organization https://dev.azure.com/example \
  --project "Team Project" --id 12345 --tail-lines 80 --json
tvh cloud read --json az pipelines runs list --organization https://dev.azure.com/example \
  --project "Team Project" --result failed --top 3
tvh sonar read --json qualitygates/project_status projectKey=example pullRequest=123
tvh ado run watch --organization https://dev.azure.com/example --project "Team Project" \
  --run 12345 --max-minutes 29 --timeout 1800
tvh frontend capture --url http://localhost:3000 --name home --json
tvh frontend compare --before /tmp/baseline/capture --after /tmp/current/capture --json
tvh greenfield init --target /tmp/new-service --profile service --json
tvh verify --repo /tmp/new-service --design --json
```

## Command conventions

Explicit workflow commands such as `review`, `verify`, and `frontend capture` have their own typed arguments. Other public operations use declared native routes. CLI controls precede `--`; arguments for the underlying operation follow it. The CLI owns interpreter selection, paths, execution limits, retained evidence and exit mapping. Native options remain available without reconstructing a script invocation.

```bash
tvh tools --check --json
tvh bundle check --json
tvh findings validate --raw -- findings.json --repo .
tvh deps read --json -- npm outdated --json
tvh servicenow get --json -- sys_script 'active=true' 'sys_id,name'
tvh dev read --json -- http get http://localhost:3000/health
tvh scaffold brief --raw -- --repo . --kind service
tvh spec list --raw -- --vault /path/to/vault --customer example
tvh orchestrate plan --raw -- --spec 'Build an API and frontend'
tvh checks iac --input-file changed.txt --json
tvh checks code-types --json -- --repo . --baseline origin/main --symbols none
tvh code types --raw -- Widget.cs --symbols none
tvh eval reviewer --timeout 1800 --json -- --engine copilot
tvh benchmark candidate run --timeout 3600 --json -- --frozen /tmp/frozen \
  --manifest-sha256 <trusted-hash> --profile profile.json
```

Use `--cwd` on native routes to set the working directory without shell chaining. `--input-file` supplies an explicit stdin file; `--input-file -` accepts piped input. IaC and scenario checks require this scope rather than silently checking an empty list. Bundle and density commands accept `--bundle-root` before `--` when operating on an alternative bundle. Native output flags and result schemas remain available after `--`.

Native routes default required output locations into their fresh evidence directory where possible. Explicit native output paths retain the operation's existing artifact/vault scope rules. CLI evidence always stays outside the source and harness checkout. Resumable evaluation queues retain their own persistent runtime state. Set the outer CLI timeout to cover native time budgets, grading and build overhead; it may be 1..86400 seconds per dispatched operation.

`--json` emits the versioned execution envelope. `--raw` emits complete native stdout without banners or truncation, preserving existing JSON/text pipelines while still writing `result.json` and logs separately. These modes are mutually exclusive. Without either, human output previews are bounded. Native exit codes remain in the result even when the CLI normalizes them. Inspect the result's status and native diagnostics before treating a check as complete.

Use an explicit baseline from the PR or repository configuration. `HEAD` selects local edits only. Review computes the merge base of the supplied baseline and HEAD, then includes tracked staged and unstaged changes. Untracked files make review incomplete; the CLI neither stages nor opens them. Inspect and stage intended files separately. Tracked dotenv changes are refused. Filenames containing newlines are unsupported by the existing reviewer input contract.

`--context-file` supplies review topics, specs, and prior check evidence as untrusted data. The independent reviewer retains the existing provider-specific restrictions and JSON findings. Review does not execute verification, approve, fix, commit, or push. The review-and-fix playbook owns the surrounding process. No second reviewer is required merely because the CLI used a provider process.

`verify` uses the installed project verify, falling back to the repository's `scripts/verify.sh`. A missing command is incomplete. It executes through the existing verification runner and references its receipt. `--fast` forwards that option to the project verify. A project-specific command documented elsewhere still needs explicit execution and evidence.

`greenfield init` writes design skeletons and the external project verify without overwriting existing content. Initialize Git for a standalone repository before recorded verification. `verify --design` forwards design-only verification; it is mutually exclusive with `--fast`. The CLI supplies its bundle path to the verify template so custom installation paths do not silently skip design checks. An unavailable design gate is incomplete verification.

`frontend capture` opens localhost pages only. It retains screenshots and `capture/report.json` under the CLI evidence directory. Native capture findings remain information for visual review; successful capture does not establish usability or accessibility compliance. `frontend compare` normalizes the native tool's regression exit 2 to CLI exit 1. A missing or invalid report is CLI exit 2. Reports must cover the same screens and agree on axe coverage.

`ado run watch` streams human-readable events while retaining complete output. JSON mode returns one envelope when the watch ends. A completed unsuccessful pipeline is CLI exit 1; timeout or read failure is exit 2. Set `--timeout` to cover `--max-minutes` plus request overhead. Streaming previews remain bounded; the full event log remains in the evidence directory.

## Results and evidence

Noninteractive operational commands support `--json`, `--raw`, `--out`, and `--timeout`. JSON options must precede the raw provider arguments of `cloud read`. Output directories must be fresh and outside both the source and harness checkout. The default is a private temporary directory. Logs remain there until removed by the caller or normal temporary-file cleanup; retain required evidence in approved artifact storage.

| Exit | Meaning |
| --- | --- |
| 0 | The operation completed, or review had no applicable tracked changes |
| 1 | A completed check failed, or review returned findings |
| 2 | Invalid input, missing prerequisite, refusal, malformed results, timeout, or incomplete execution |

For diagnosis, exit 0 means the read completed, not that the pipeline passed or the agent established a cause. `doctor` checks local executable availability without running provider commands or checking credentials. Its output does not establish skill discovery or authentication.

The version 1 JSON envelope contains `command`, `status`, `scope`, `steps`, `artifacts`, and `data`. Executed operations also record `harness` provenance and hashes of CLI-specific inputs. Errors add `error`. Status is `completed`, `findings`, `failed`, `incomplete`, or `not-applicable`. Each executed step records argv, underlying exit status, timeout state, duration, and stdout/stderr artifact paths. Native findings and verification receipts retain their formats. `result.json` records the same envelope; it is an execution record, not approval or an attestation.

Human output previews at most 12,000 bytes per stream and links to the complete logs. JSON references complete artifacts instead of embedding potentially unbounded logs. Review retains source commit/state information and rejects source changes during execution. A reviewer response with dropped findings is incomplete, even if the surviving list is empty.

## Effects and boundaries

| Command | Effects and enforcement |
| --- | --- |
| `doctor`, `context select` | Local inspection and evidence writes |
| `verify` | Executes repository code and may build artifacts or use the network; existing verification receipt semantics apply |
| `review` | Reads the tracked diff, writes evidence, and calls the selected provider; existing reviewer restrictions apply |
| `ado run diagnose` | Restricted Azure DevOps GETs through [ado-run-failure.sh](../azure-devops/ado-run-failure.sh); existing identity and redaction behavior applies |
| `ado run watch` | Restricted repeated GETs through the existing watcher; does not queue or retry |
| `cloud read`, `sonar read` | Existing restricted read wrappers; no new write verbs or credential access |
| `greenfield init` | Writes design skeletons and an external project verify; no source implementation or deployment |
| `frontend capture`, `frontend compare` | Local browser capture and artifact reads; no app startup or remote-host override |
| `eval skills` | Explicit native model calls with skill/file-reading tools only; local traces and model usage |
| Remaining catalog commands | Effects are declared per route in [the catalog](commands.md); local execution, network reads, artifact writes, installations and external writes remain distinct |

The CLI dispatches argument arrays, not shell command strings. Command help and `doctor` do not start authentication or installation. Pinned tool installation, dependency builds, local execution and external writes are separate declared operations, never automatic preflight actions. External writes such as posting PR findings retain the existing pipeline identity and require authorization; adding a route does not authorize posting. No broad allow rule is installed. Human-only container login, MSAL state production and review-comment mining require `--interactive` in a terminal, reject JSON/raw capture and inherit terminal input/output without credential logs. Tool and TTY checks are guardrails, not proof of human identity or a sandbox. No route queues or retries a pipeline. Read-wrapper output redaction remains best effort. Verification logs can contain sensitive consumer output; use the existing access and redaction policy. The Bash hook recognizes the supported CLI cloud-read form and continues to reject mutations and command chaining. Identity permissions remain the real boundary.

Timeouts terminate the process group on POSIX and use `taskkill /T` on Windows. The timeout bounds each dispatched operation, not the total duration of a multi-step process. Syntax errors print normal argument help with exit 2; operational failures return the JSON envelope when requested.

## Validation and remaining evaluation

[test_cli.py](../../../tests/test_cli.py) covers explicit workflows and installation. [test_cli_catalog.py](../../../tests/test_cli_catalog.py) checks exhaustive file classification, offline help for every route, real local tool dispatch, stdin scope, raw JSON compatibility, native exits, artifact paths, wrapper refusals and human-only boundaries. The deterministic suite makes no provider or remote service calls. Private libraries, provider/grader adapters, hook protocols and snapshot fixtures remain internal; their owners are recorded in the catalog. Direct CI implementation calls may remain.

The [pilot evaluation cases](../../../benchmarks/cases/process-skills.json) distinguish expected native skill selection from workflow outcomes. Run a selected case explicitly with a pinned provider model:

```bash
tvh eval skills --engine copilot --model <exact-model-id> \
  --only review-change --only explain-reviews --repeats 3 --json
```

Use `--all` to run every case. An exact model and an explicit case selection are required; no model calls run during installation or `doctor`. The runner creates temporary native project skills, permits only file-reading and skill tools, and retains raw JSON events, native usage, client version, input hashes, and observed tool calls. It never modifies personal skills or authentication. Claude uses project settings with external integrations disabled; Copilot disables custom instructions and built-in external integrations. Personal client configuration or skills may still affect discovery, and tool restrictions are not a sandbox.

Only a model-issued native `skill`/`Skill` call counts as invocation. A response claiming to have used a skill does not count. Missing terminal events, malformed traces, failed processes, and timeouts are incomplete. A completed selection mismatch returns exit 1. The report assesses native selection, observed conditional reference reads and synthetic handoff inspection, marks completed workflow outcomes unassessed, and leaves unavailable metrics null. Pipeline cases select debugging and expect no dedicated pipeline skill. Full workflow, adapter parity, quantitative adoption thresholds, and token-efficiency comparisons remain separate evaluations. See the [accepted CLI decision](../../../docs/adr/0009-process-skills-and-unified-cli.md).

The native discovery and tool restrictions follow the clients' installed CLI help and the [GitHub CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).
