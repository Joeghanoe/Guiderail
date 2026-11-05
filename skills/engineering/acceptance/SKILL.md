---
name: acceptance
description: Prepare runnable business acceptance plans and record their evidence for stakeholder sign-off. Use for UAT or business test sheets; automated unit and integration tests use test instead.
---

# Prepare business acceptance

Inputs are approved criteria, the business process, target environment and responsible business owner. Read [the business test plan procedure](WRITE-BUSINESS-TEST-PLAN.md) when producing a workbook. Preserve requirement provenance and describe observable outcomes in the tester's language.

```bash
tvh testing business-plan --raw -- <plan-spec.json> <business-test-plan.xlsx>
```

Keep the plan specification beside the workbook. Include preconditions, roles, expected results, evidence and cleanup ownership. A missing implementation remains a visible gap. Generated workbooks and unchecked rows do not count as execution or acceptance.

Hand the runnable plan, evidence links, untested criteria and open questions to the business owner. The agent prepares and records; the business owner accepts the outcome and existing release authority remains unchanged.
