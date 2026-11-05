# Implement a bounded slice

Start from agreed criteria and the affected interfaces. Keep requirement identifiers attached to work packages and tests. Do not silently narrow a criterion to what the existing code already supports.

Select applicable rules and inspect repository conventions. For a defect, first retain a failing test at an appropriate public boundary. For new behavior, implement a coherent slice with meaningful tests rather than building every technical layer in isolation. Keep I/O, time and configuration injectable and avoid unrelated refactoring.

Run the focused check after each meaningful change, then the required project gate. When checks fail, retain the failing output and fix or report the issue. Never convert a timeout, missing runtime or skipped test into a pass. Re-run verification after remediation and tie receipts to the current source state.

Output the source scope, original criteria, implemented behavior, test and verification artifacts, and unresolved decisions. Independent review receives failures as well as successes. Do not pass a stale receipt from before the final edit as proof of the final state.
