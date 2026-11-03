# CODE.5 responsibility review

Assess responsibility independently of the structural checker. Read the task, rule and Boundary, design, changed component and relevant callers. Record missing context as inconclusive.

| Score | Evidence |
| --- | --- |
| 0 | Concrete responsibility mixing or leaked dependency decisions cause a demonstrated defect or maintenance coupling. Name paths, trigger and consequence. |
| 1 | A material responsibility concern remains unresolved. Trace the coupled responsibilities and explain why the accepted boundary does not apply. |
| 2 | The task follows the responsibility boundary, with a bounded concern or uncertainty explicitly recorded. |
| 3 | Responsibility and dependency ownership are supported by design, callers and behavior evidence, with no material concern in scope. |

Use not-applicable for an accepted exception and inconclusive when the evidence cannot establish a judgment. Scores 2 and 3 meet this proposed rubric; a score never overrides a deterministic failure or grants human approval. Human review resolves disputed applicability, threshold-crossing disagreements and material uncertainty.

A result records requirement ID, source revision, reviewed artifact revision, score/status, applicable exception, paths/lines, evidence, trigger/consequence, uncertainty and reviewer/model version. Preserve independent judgments before adjudication. The coding agent must not generate its own acceptance judgment.

Do not substitute file count, class length, method count or interface count for this assessment. Calibration against accepted positive, negative and boundary cases is required before using a model score as a gate. The initial implementation leaves this review pending in execution summaries.
