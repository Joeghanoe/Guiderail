# Local backup evaluation contract v2

Functional scope: F01-F16 (v1 is F01-F10 plus the additions below), local synthetic data, .NET 10, a 60-minute candidate execution budget and no parallel coding agents. Model/provider selection is run metadata, not a task constraint. This contract supplies an automation boundary; internal architecture and backup representation are free.

## Invocation

The evaluator launches a fresh process for every operation: `<command argv...> <absolute-request.json> <absolute-response.json>`. The candidate implements this entrypoint or a thin adapter to its application. The adapter is candidate code and subject to the same review. It must not manufacture outcomes instead of invoking the application. No shell expansion is used. All paths are absolute. Write one JSON object to the response file and exit 0 for a handled operation, including expected failures. Crash, timeout or malformed response fails the check. Diagnostic stdout/stderr and response `logs` are operational output and must omit sensitive payloads.

## Requests

All requests contain `operation`. Backup and restore use `store` and `run_id`.

- `backup`: `now` (UTC ISO timestamp), `retention_days` (30), and `sources` with unique `id`, `kind` (`files` or `git`) and `path`. A files source is a directory; preserve its relative paths and bytes. Git sources require committed worktree content, branches, tags and reachable history. Untracked files, Git hooks and machine-specific Git configuration are not required backup content.
- A source may contain `fault: "read"` and a synthetic `fault_message`. This is a local test seam for a deterministic source-read failure. Fail that source as an I/O error and continue healthy sources. Missing source paths are also failures. Do not echo raw fault text to operational output.
- `restore`: `destination`. Restore sources underneath `<destination>/<source-id>/`. Reject an occupied destination; never overwrite its contents. No source paths are provided to restore.
- `schedule`: `now`, `last_success_at` (UTC timestamp or null). Return `due`: true when no prior successful run exists or its UTC calendar date is earlier than now's date. This exercises daily scheduling logic, not a production scheduler or an RPO guarantee.
- `retention`: `now`, `retention_days`, `points: [{id, created_at}]`. Return `eligible` as a list of the `id`s of exactly the points whose creation plus retention_days is <= now. This is a simulation; perform no deletion.

## Responses

Always return `status`: `succeeded`, `partial`, `failed` or `rejected`. Backup responses additionally contain:

- `run_id`, `restore_point` (the run ID), `created_at` and `completed_at` (UTC ISO timestamps);
- `sources: [{id, status, code}]`, exactly one outcome per requested source; `code` is a safe reason code for failed sources, and null or absent for successes;
- `object_count`, `byte_count`: totals of successfully backed-up logical files; for Git count committed worktree files at HEAD, excluding `.git` internals. Empty files count as objects;
- `artifacts`: nonempty list of relative paths to payload files inside `store`. The grader uses these to inject storage corruption; paths must resolve inside the store. Include payload, not report files;
- `health`: `healthy` for success, `degraded` or `unhealthy` for incomplete runs;
- `alerts`: list of `{run_id, source_id, code}` entries for failed sources (empty on success).

Restore responds with `status` and `sources: [{id, status, code}]`. Corrupt/missing payload must not be reported as successfully restored. Partial writes may remain only in the newly created destination; the overall outcome must explain the failure. Reusing a run ID must reject or return its existing result without changing any existing recovery point. New run IDs preserve independently restorable versions.

## Evidence and boundaries

The public F01-F10 criteria accompany this contract. The grader checks restored bytes, Git refs/history, source/destination preservation, counts, failure outcomes, retention boundaries and output leakage. It does not accept candidate test claims as proof. It uses synthetic fixtures, independent hashes and Git. Cloud integration, WORM, actual SQL import/export and production service levels are outside this scenario.

The grader accepts any executable argv. A separately recorded build verifies .NET 10; a passing functional grade alone cannot prove the implementation language or architecture. CODE.5 and policy/behavior evidence are separate dimensions. The local subprocess runner is **not a sandbox** and never claims isolation. Use an enforced isolated environment for an authoritative run. Otherwise all-pass functionality remains an exploratory result with overall status inconclusive. Freeze grader/contract/prompt/fixture hashes before launch. A run profile must record provider, model, options, adapter, starting commit, tools, permissions, 60-minute execution limit and trace location. Missing usage/cost data stays null, never zero.

## v2 additions (F11-F16)

- `backup` may carry `dry_run: true`: discover and report (`status`, `sources`, `object_count`, `byte_count`, `dry_run: true`, `artifacts: []`); write nothing to the store, create no recovery point and do not use up the run ID.
- A `files` source may carry `exclude`: a list of glob patterns (`*` matches any characters including `/`) matched against the path relative to the source directory. Excluded files are not stored and not counted. The response has `excluded: [{source_id, path, reason}]` with the relative path and a safe reason code.
- `status`: request `store`, `run_id`. Response `status: succeeded` and `run: {run_id, state, created_at, completed_at, sources: [{id, status, code}], object_count, byte_count}` where `state` is the run outcome (`succeeded`, `partial`, `failed`). Unknown run: `status: rejected`, `code: run_not_found`. No writes.
- `health`: request `store`. Response `status: succeeded` and `health: healthy` when the store is a usable directory; otherwise `status: failed` and `health: unhealthy`. No writes, also not to an unusable store.
- Backup responses carry `events`: a list of objects with `event` (`RunStarted`, `SourceStarted`, `SourceFinished`, `RunFinished`) and only the properties `run_id`, `source_id`, `outcome`, `code`, `object_count`, `byte_count`, `duration_ms`. One `RunStarted` first, one `RunFinished` last (its `outcome` is the run outcome), and for each source a `SourceStarted` then a `SourceFinished` (outcome and, when failed, `code`).
- `run_id` and source `id` values are untrusted. A value containing a path separator, `.`, `..` or an absolute path is rejected (`status: rejected`) on backup, restore and status, and nothing is written outside `store`.
