# Playbooks

* [Add an example case](add-example.md) - Turn real code that follows or breaks a rule into a case with a concrete good and bad example.
* [Analyse ServiceNow configuration](analyse-servicenow.md) - Answer "why does ServiceNow do X" or "what breaks in this migration" by reading configuration through the read wrapper, and write down any change as steps for a human.
* [Classify a test failure](classify-test-failure.md) - Sort a failing test into product, test, environment or flaky before anyone changes code.
* [Diagnose a failed pipeline run](diagnose-pipeline-failure.md) - Read why an Azure DevOps run failed, classify the cause, and propose a fix in the repo without touching the pipeline or cloud.
* [Draw an integration diagram](draw-integration-diagram.md) - Turn an integration analysis into a one-page draw.io diagram (which component talks to which system, through what) by writing a spec for the diagram generator, never new drawing code.
* [Orchestrate a workload across specialized agents](orchestrate-workload.md) - Decompose a milestone, backlog item, or complex change into bounded subagent work packages with cost-effective model tiering and lead review.
* [Process feedback on the harness](process-feedback.md) - Turn a correction, a rejected finding or a missed defect into a proposed case, and decide what the harness should learn.
* [Review a change and fix what is safe to fix](review-and-fix.md) - Run the deterministic gate, review the local diff with the review playbook, fix the findings an agent may fix, and hand the human the end result with a receipt.
* [Review a change](review-change.md) - Review a diff against the selected rules and their cases; every finding cites a rule ID and evidence.
* [Triage a production or environment incident](triage-incident.md) - Investigate a reported incident ("something is broken", "errors in prod", "users are seeing failures"), classify the root cause, and produce an actionable report without changing any running system.
* [Verify a deployment to DEV, TST, ACC or PRD](verify-deployment.md) - After a pipeline finishes, confirm the right version is running, the health endpoint responds, and App Insights shows no new errors — read-only, through the harness wrappers.
* [Verify a frontend change by looking at it](verify-frontend.md) - Screenshot what was built at phone, tablet and desktop widths, run the automated WCAG and responsive checks, and judge the result against the people who will use it.
* [Write a business test plan](write-business-test-plan.md) - Turn the process behind a change into a short end-to-end test plan in Excel that a project manager or business owner can follow, run and sign off.
