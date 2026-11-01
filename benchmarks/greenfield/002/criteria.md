# Acceptance criteria F01-F16

All criteria must pass to call local functionality complete. The evaluator is separate from your code, computes expected content independently and uses a fresh directory per check. See `CONTRACT.md` for the invocation. These are observable requirements; the evaluator's checks are not published.

| ID | Observable requirement |
| --- | --- |
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

| F11 | A status call reports the run ID, state, UTC creation time, source outcomes and counts of a stored run, leaves the store untouched, and reports an unknown run as `run_not_found`. | | F12 | A health call reports a usable store as healthy without writing, and an unusable store as unhealthy with a failed status. | | F13 | A dry run reports the objects and bytes a backup would copy and the source outcomes, creates no recovery point and writes nothing, and the same run ID can still be used for a real backup. | | F14 | Excluded files are neither stored nor counted, each is listed with its source, relative path and a reason, restored content excludes them, and sources are not modified. | | F15 | A backup reports exactly the events in the contract, in order, each with the run ID, a code on failed sources, and no property or content outside the contract. | | F16 | Hostile run or source identifiers (traversal, absolute paths, separators) are rejected on backup and restore and nothing is written outside the store. |

F03, F10 and F16 are security hard gates: a failure there fails the run regardless of other results. CODE.5 (one responsibility per file) and the design checks D01-D09 (a solution design, ADRs, the repo's own AGENTS.md, a verify command, a composition root, interfaces, operational contract, tests per layer) are checked separately as the architecture dimension.
