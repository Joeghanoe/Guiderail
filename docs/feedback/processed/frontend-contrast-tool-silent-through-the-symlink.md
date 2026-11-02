---
type: Example
title: "C-NNN A contrast check run through the harness symlink prints nothing and exits 0 for failing colours"
description: tools/frontend/contrast.mjs decides it was run directly by comparing import.meta.url with argv[1], which differs when the harness is reached through a symlink, so it does nothing and passes.
example_id: C-NNN
rule: /rules/frontend/ui-1-look-at-what-you-built.md
verdict: automation-candidate
status: processed
tags: [frontend, contrast, tooling]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-01T18:00:00Z }
sources:
  - id: evidence
    resource: a project session that ran ~/.golden-path-harness/harness/tools/frontend/contrast.mjs (a symlink to the harness checkout) on two failing colour pairs and got no output and exit code 0; the same command from the real path failed both with exit 1
---

# Situation

A script guards itself with "only run when started directly" by comparing `import.meta.url` with `pathToFileURL(process.argv[1])`. When the harness is installed as a symlink, `argv[1]` is the symlink path, the comparison is false, and the check silently does nothing and exits 0.

# Why (verdict)

A check that cannot run must fail, not pass (OBS.2 states the same for alerts). Here a failing colour pair passes through an agent or a CI step that uses the documented path. Resolve both sides with `fs.realpathSync` before comparing, or drop the guard, and add a test that runs the tool through a symlink.

# Compliant pattern

Compare `realpathSync(fileURLToPath(import.meta.url))` with `realpathSync(process.argv[1])`.

# Disposition

Owner declined E-046 on 2026-11-01 as too specific for a reviewer example. Excluded from the new eval cases.
