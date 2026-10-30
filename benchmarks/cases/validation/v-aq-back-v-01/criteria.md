# Criteria v-aq-back-v-01 (hidden from the candidate)

Functional
- G01 A new dataset member exists with a kebab-case key from the single key mapping; stored keys of existing datasets are unchanged.
- G02 It is registered in the dataset registry once and picked up by the per-subscription orchestration without a second list.
- G03 One activity follows the existing activity pattern: load-state checkpoint per subscription via the registry's pipeline-name helper, window handling, write to the lake only when there are rows, metrics and log with run identifiers and counts.
- G04 The service method and its interface member map only the five requested fields; missing fields do not throw.
- G05 The API version is a named constant next to the others; the base URL and path are not typed twice.
- G06 A default cadence entry exists for the new dataset, in the same place as the others.
- G07 All requests go through the existing resilient sender (shared budget, 429/503 handling); no new HttpClient and no in-process retry loop.
- G08 A unit test with a stub HTTP handler covers the mapping and the URL, without a network.

Rules checked: CODE.4 (the dataset name, activity name and key are not retyped as literals), CODE.7 (a doc or setting that lists datasets is updated if one exists in the snapshot), CODE.8 (collaborators come in through the constructor and are registered in the composition root), T.2 (no clock or HTTP created inside), T.5 (a scenario or test states the intent), SEC.3 (no key or connection string), OBS.3 (named metric, identifiers and counts, no payload in logs).

Hard gates
- The solution builds and the existing tests pass (T.1).
- No secret, tenant id or subscription id is written into code, tests or logs (SEC.2, SEC.3).
- The existing datasets still resolve to the same stored keys (regression otherwise).

Regressions
- Adding the dataset to the machine-learning set, or to the "once per parent run" path.
- Changing the order or the keys of existing registry entries.
- A catch that returns an empty list for every failure status.
