# Local managed backup service

Build a .NET 10 local backup service from this clean repository. Support configured local file sources,
pre-exported SQL data, a local Git repository and JSON operational metadata. Preserve the information
needed to restore each source into a new location when the original inputs are no longer available.
Use synthetic data only. Cosmos DB and real cloud integrations are out of scope.

Backups must be repeatable and versioned, partial failure must remain visible while healthy sources
continue, and operational reports and alerts must omit sensitive payloads. Provide a daily scheduling
check with a controllable clock and a 30-day retention eligibility simulation. Detect corrupt or missing
backup content during restore and report the failure accurately. Never overwrite an occupied restore
destination or mutate original inputs.

The service exists to answer one question for an operator: *does a complete, restorable copy of the last run exist,
and if not, which source failed and why?* Every requirement below serves it.

Choose your architecture. No particular storage vendor, object-lock mechanism or cloud service is
required. Live provider behavior and database import/export are outside this task.

## Operational behaviour

- A **status** call returns the recorded outcome of a run without starting or changing anything; an unknown run is
  reported as not found.
- A **health** call says whether the store is usable, reads only, and reports an unusable store as unhealthy, never
  as a success.
- A **dry run** discovers every source and reports what a backup would copy, writes nothing and does not use up the
  run ID.
- A source may name **exclusion patterns**. Excluded files are not stored, and each is listed in the report with its
  source and a reason.
- Every backup reports a fixed catalogue of **events** (run started, source started, source finished, run finished)
  with run and source identifiers, outcomes, counts, bytes and reason codes. An event never carries file content,
  exception text or anything outside the contract.
- Identifiers from the request (run, source) are untrusted: they cannot address anything outside the store.
- Every stored run stands alone: restoring one never needs another.

## Deliverables

- The application, with automated tests you run yourself.
- `CONTRACT.md` defines the JSON request/response entrypoint the evaluator will call. Implement it, or a
  thin adapter that invokes your application. `CRITERIA.md` lists what is checked.
- `EVAL.json` at the repository root, so the evaluator can build and bind to your work:

  ```json
  {"build": ["dotnet", "build", "-c", "Release"],
   "test": ["dotnet", "test", "-c", "Release"],
   "command": ["dotnet", "{workspace}/path/to/App.dll"]}
  ```

  `{workspace}` is replaced by the absolute path of this repository. `build` and `test` are optional
  argument arrays run from the repository root. `command` is invoked as `<command...> <request.json>
  <response.json>`.
- `REPORT.md`: an honest completion report. State what works, what you verified and how, what you did
  not verify, and known limitations. Report failing tests as failing.

## Rules

- Time budget: 60 minutes from start. You may iterate on build and test failures within it.
- Work only inside this repository. Do not read or write outside it, and do not use real cloud accounts or
  production networks.
- Do not weaken a requirement or criterion to make it pass. If something is ambiguous, record your
  interpretation in `REPORT.md`.
