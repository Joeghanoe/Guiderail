# Greenfield scenarios

These scenarios ask a candidate to build a new service. The task and acceptance requirements describe expected behavior; the independent evaluator implementation remains separate. Scenario configuration identifies the inputs used for a run.

| Scenario | Assignment | Candidate task | Acceptance requirements | Configuration |
| --- | --- | --- | --- | --- |
| 001 | Local managed backup baseline | [Task](001/task.md) | [Acceptance requirements](001/criteria.md) | [Scenario](001/scenario.json) |
| 002 | Local managed backup service | [Task](002/task.md) | [Acceptance requirements](002/criteria.md) | [Scenario](002/scenario.json) |

Use the [benchmark navigation](../README.md) for other evaluation entry points and the [brownfield case guide](../cases/README.md) for the train, validation and holdout boundaries. This index is evaluator navigation, not an additional candidate input.

## Candidate instruction adapters

The scenario sources retain the candidate instruction adapters for [001](001/CLAUDE.md) and [002](002/CLAUDE.md). Their `@` references are resolved in the materialized candidate workspace, not this source folder.

## Contracts and evaluator

Scenario 001 supplies [contract v1](../local-backup-contract.md) as `CONTRACT.md`; scenario 002 supplies [contract v2](../local-backup-contract-v2.md). The [backup evaluation guide](../local-backup-evaluation.md) documents the independent grader and original calibration scenario.
