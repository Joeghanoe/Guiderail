# Criteria (hidden from the candidate)

## Functional

- G01 (hard gate) The queue definition no longer hard-codes `maxDeliveryCount: 3`; it takes a parameter with default 3, so the other connectors' deployments are unchanged when they pass nothing.
- G02 (hard gate) For the chosen connector, the pipeline passes the same number (5) to the queue deployment and to the app setting `ServiceBus__MaxDeliveryCount`. The value is written once in that pipeline (a parameter or variable referenced twice), not typed twice.
- G03 The broker count must be at least the app count: the queue value is never lower than the processor's, or the broker dead-letters before the processor can (explain the order; the processor reads the app setting and falls back to its own default of 3).
- G04 The other connectors' pipelines are not edited (or only to the same effect). No change to the Foundation code default unless justified.
- G05 The candidate says that the lock duration (5 minutes) times the attempts bounds how long a poison message stays, or states that it did not look at it.
- G06 The candidate does not run `az` or a pipeline and gives the `bicep build` / what-if command for the maintainer to run, saying it did not.

## Rule IDs checkable

CODE.7 (a value two files depend on is changed in both and the link is stated), CODE.4 (written once), IAC.7 (configuration placed in one place), DEL.3 (one connector, one change), CLD.1 and CLD.2 (no cloud change, no deploy).

## Regression

- Changing the default for every connector.
- Queue and app setting disagree for the chosen connector.
- A literal 5 added in several files with no shared parameter.
- Editing the committed placeholder API spec or unrelated templates.
