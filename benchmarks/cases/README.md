# Evaluation cases and the train / validation / holdout split

Cases are brownfield: a change task on an existing codebase, with hidden acceptance criteria.
Greenfield scenarios stay in `benchmarks/greenfield/`. The runner does not execute brownfield cases yet.

| Role | What it is for | Where it lives | May teach the harness |
|---|---|---|---|
| train | source of examples (`harness/examples/`) | no cases | yes |
| validation | choose between harness changes; run often | `benchmarks/cases/validation/<id>/` | never |
| holdout | sealed; run at release only, never read while tuning | `~/.harness-evaluation/holdout/` (outside the repo) | never |

- One component has one role. A pattern seen in a train component may reappear in a validation case; that
  tests generalisation. Do not turn a validation or holdout case into an example, a rule edit or a template.
- A case holds `task.md` (what the agent is asked), `criteria.md` (hidden checks and rule IDs), `case.json`,
  and `snapshot.json` (neutral file paths plus sha256, because the sources have no Git metadata).
- The map from neutral aliases to real paths is private (`~/.harness-evaluation/private/`) and is the only place
  real names appear. Repo content carries none (`harness/templates/project-terms.txt`).
- Boundary examples need a human owner. Candidates without one are parked in
  `~/.harness-evaluation/pending-boundary/` until a person accepts the deviation.
