# Change log

## 2026-11-01

- Adopted one central YAML configuration location for deployment settings and resource names, with run choices exposed as clearly labelled parameters. Added and approved E-044, E-045 and E-049. The owner-run Azure pipeline confirmed the runtime-variable composition after the original nested compile-time assertion failed.
- Aligned the GitHub Actions example E-047 with the shared/environment YAML convention. Adapted the inspected reference repository's reusable loader and environment workflow; kept source refs consistent and used JSON outputs for workflow consumers.
- Added and approved E-037, E-038, E-041 and E-048 for APIM product access, authorized cloud reads, guard clauses and simple conditional expressions, including a switch alternative. Eight new examples produced 15 passing scenarios with AGY `gemini-3.8-flash-high` through eval-queue on bundle `c3bf11769e`.
- Promoted E-021, E-023, E-024, E-025, E-027, E-028, E-029, E-030, E-031, E-032, E-033, E-035 and E-036 using the owner's acceptance and complete historical passing scenario sets. Preserved model-specific failures and the original advisory/gating classifications in the recorded results.
- Kept BannedSymbols/analyzer files and scenario-mapping machinery opt-in for consumer repositories. Corrected setup guidance and added scaffold regression coverage. The owner declined the narrower E-039, E-040, E-042, E-043 and E-046 reviewer cases.
- Recorded prior owner adoption of CODE.8, CODE.10, DEL.4, DEL.5, OBS.3, T.6 and start-greenfield from targeted merged PRs, with approval commits on those documents. Marked the tested design-check and OpenAPI-drift gate descriptions stable.
- Recorded the owner's explicit approval of CODE.7, CODE.9, CODE.11, OBS.2, UI.1, UI.2 and the remaining operational playbooks. The owner confirmed write-business-test-plan had supported acceptance testing. All active rules, gates and playbooks are stable.
- Removed E-034 and its dedicated fixture at the owner's request. Historical eval evidence, including its failed bad case, remains in the result records; its identifier is not reused.
- Recorded the owner's approval of [ADRs 0001–0007](../docs/adr/). Kept ADR 0008, the development-process proposal and the knowledge-base incident-triage automation idea open for separate review.
- Moved processed feedback to [docs/feedback/processed](../docs/feedback/processed/), retained the [current conventions](../docs/decisions/feedback-conventions.md) as an editable record, and documented [example verdicts, lifecycle and evaluation results](../docs/example-verdicts.md). Removed the temporary draft-approval audit after preserving useful provenance.
- Adopted this OKF `log.md` summary format from Vegviser. Entries describe material changes and rationale, newest date first; Git retains the authoritative diff and history. Current conventions and ADRs retain their own authority and lifecycle.
