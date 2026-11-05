# Example verdicts, status and eval results

These describe different things. A verdict classifies an example's situation, status records its maturity, human verification records acceptance, and an eval result measures reviewer behavior. Passing an eval does not approve a convention.

## Verdict

| Value | Meaning | Reviewer eval behavior |
| --- | --- | --- |
| `violation` | The described situation breaks the linked rule. | Generate bad cases that must be flagged and good cases that must not be flagged. |
| `compliant` | The described situation demonstrates following the linked rule. | The same good/bad scoring applies; the verdict describes the situation, not every code block in the document. |
| `boundary` | A legitimate exception or limit on where the rule applies. | Test the good side for false positives. Keep this example visible to the reviewer because its accepted exception is the behavior under test. |
| `open` | The proposed interpretation has not been decided. | No reviewer scenarios. |
| `rejected` | The feedback or proposed exception was rejected, for example because it contradicts a principle or hard rule. | No reviewer scenarios. Keep the rejection reason if the record is retained. |
| `automation-candidate` | The lesson should become a tool, check or workflow rather than just a review instruction. | No reviewer scenarios. Test the resulting automation directly. |

Verdict does not track implementation progress. E-016 is a concrete example: it records the original Sonar automation proposal, but [sonar-read.sh](../harness/tools/sonar/sonar-read.sh) and its deterministic tests now implement it. Record that implementation in the editable decisions; do not change it to a violation just to create an LLM eval.

## Status and human verification

`draft` means proposed. `stable` means accepted for use. They do not mean that an implementation or reviewer is infallible.

The evaluator specifically checks `verified: { by: human:<id>, at: <timestamp> }`. Eligible examples without human verification are advisory, even if their status says stable. Human verification makes their scenarios gating. Reviewer-behavior cases are an explicit exception and gate even without this metadata.

To promote a draft example:

1. Review the situation, linked rule, verdict and good/bad code. Resolve conflicts with accepted examples.
2. Run its scenarios and investigate missed findings, false positives or execution errors.
3. Obtain explicit human acceptance and record `status: stable` plus the human-verification metadata. An agent records actual acceptance; it does not infer approval from a passing model score.

Only the selected scenarios were tested by a scoped run. Passing new cases does not verify older drafts or establish a full-suite pass. Rules, gates and playbooks need acceptance and evidence appropriate to their purpose; they do not become stable automatically because an example passed.

## Eval result

| Result | Meaning |
| --- | --- |
| `pass` | The reviewer produced the findings required by the scenario and avoided its forbidden findings. |
| `fail` | The review completed but missed a required finding, raised a forbidden one, or exceeded the scenario's finding limit. |
| `error` | The review could not be evaluated, for example because of authentication, quota, timeout or invalid output. It stays pending in eval-queue. |

An advisory scenario can pass or fail without affecting the gate. The gate is the aggregate threshold over eligible gating cases, not a substitute for examining failures. `partial` means only selected scenarios were run.

The executable definitions are in [eval.py](../harness/tools/review/eval.py), [eval-queue.py](../harness/tools/review/eval-queue.py) and [bundle.py](../harness/tools/harness/bundle.py). The [reviewer evaluation guide](../harness/tools/review/README.md) describes execution, masking and evidence. Current decisions and their evolution are in [feedback conventions](decisions/feedback-conventions.md).
