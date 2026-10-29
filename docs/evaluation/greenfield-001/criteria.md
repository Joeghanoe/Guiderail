# Acceptance criteria F01-F10

All criteria must pass to call local functionality complete. The evaluator is separate from your code,
computes expected content independently and uses a fresh directory per check. See `CONTRACT.md` for the
invocation. These are observable requirements; the evaluator's checks are not published.

| ID | Observable requirement |
|---|---|
| F01 | Back up every enabled synthetic source (files including empty and binary, a SQL export, a Git repository with history, branch and tag, and JSON metadata) and identify each source outcome. Restored bytes and Git refs/history match. |
| F02 | Restore remains possible when the original sources are unavailable, using a new process and only the stored backup. |
| F03 | Restore never overwrites an occupied destination, and sources are never modified. |
| F04 | A failed or unavailable source cannot produce a successful overall report. Healthy sources still complete, and the report names the affected sources. |
| F05 | Backup versions are recoverable independently. Reusing a run ID is rejected or returns the existing result without corrupting any backup. |
| F06 | Daily backup intent (UTC) and 30-day retention can be exercised with a controlled clock. A point becomes eligible at creation plus 30 days, exactly. |
| F07 | Corrupt or missing backup content cannot be reported as a successful restore. |
| F08 | The operator report exposes run ID, UTC times, source outcomes, object and byte counts, recovery point identifiers and failure reason codes. |
| F09 | An incomplete backup produces a local alert and degraded or unhealthy evidence naming the affected sources and run ID. A healthy run is healthy. |
| F10 | Logs, alerts and reports contain no payload or credential content. |

F03 and F10 are security hard gates: a failure there fails the run regardless of other results.
CODE.5 (one responsibility per file) is checked separately as an architecture dimension.
