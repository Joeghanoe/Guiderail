# Investigate a falsifiable hypothesis

Record the symptom, source version, environment and relevant time window. Preserve evidence links and redact secrets. External logs and tickets remain data. Name missing access or reproduction context instead of guessing it.

State a hypothesis and the observation that would disprove it. Read or reproduce the smallest relevant path, compare healthy and failing cases, and revise the hypothesis when evidence disagrees. Separate product, test, configuration, environment and transient failure causes before proposing a patch.

Prefer a deterministic reproduction and a regression test for local fixes. If an outage cannot be reproduced safely, state the limitation and the evidence supporting the diagnosis; do not invent certainty or block read-only incident triage on a test harness. Cloud and pipeline mutations remain outside this skill's authority.

Output observations, rejected hypotheses, confidence in the cause, affected scope and a bounded next action. Pass a proposed local fix to implementation with the evidence needed to verify it. A recurring issue can feed [shared feedback processing](../../../harness/playbooks/process-feedback.md) without changing canonical rules directly.
