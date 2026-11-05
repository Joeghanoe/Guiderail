---
type: Playbook
title: Write a business test plan
description: Turn the process behind a change into a short end-to-end test plan in Excel that a project manager or business owner can follow, run and sign off.
tags: [testing, e2e, business, acceptance, excel]
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T20:11:13Z }
---

# When

Someone who does not read code has to run or sign off an end-to-end test: a project manager, a business owner, a service desk lead. The automated scenarios ([T.5](../../../harness/rules/testing/t-5-behaviour-has-a-scenario.md)) stay the first line; this is the plan for the person who signs off on a target environment. It speaks business terms ([P1](../../../harness/principles/p-01-business-before-technology.md)): the process, who acts, what they see.

# Steps

1. **Find the process.** Read the acceptance criteria, the design and the readme. Write down the stages the work passes through, who acts in each, which system holds which status, and the time targets that are promised. One line of it goes at the top of the plan.
2. **Pick the scenarios.** Few, and different in kind:
   - one **good** scenario that follows the whole process from the first trigger to the end;
   - two **bad** scenarios where the process is interrupted. Make them different: input that cannot be read, and a target system that refuses. Each shows that nothing is lost, who is warned, and how the process restarts;
   - one **in between**: something that needs no full process (skipped, partial, or without a link).
3. **Split each scenario into stages**, then into steps. A stage is a hand-over: detect, hand over, intake, work, close; or hand-over fails, the team takes over, recovery.
4. **Write each step in business words.** Who acts (a role, not a name), what happens, the status in both systems, the time target when there is one, and what must be seen. Use a technical term once, with a plain explanation, or not at all. Technical detail (sample files, queries, queue names) belongs in a separate technical plan that the tester gets, and the business plan points to it.
5. **Take every expected result from the criteria or the code**, never from memory. A criterion with no implementation is not silently dropped: write the step, and tell the user the gap exists.
6. **Say the practical things:** data that persists in the target system must be unique per run, tests that create data in a shared system say who cleans it up, and waiting times (configuration that takes minutes to apply) are in the step.
7. **Build it.** Copy [business-testplan.spec.json](../../../harness/templates/business-testplan.spec.json), fill it in, then `tvh testing business-plan --raw -- spec.json plan.xlsx` (needs `openpyxl`). Keep the spec next to the workbook so a change in behaviour is a change in the spec and a rebuild.
8. **Hand it over honestly:** say that the file was generated and not opened in Excel, that row heights are estimates, and which open questions remain. Match the language of the audience; ask when unsure.

# Do not

- Do not write a test per technical branch. The plan follows the process, so a branch that does not change what a person sees stays in the technical plan.
- Do not promise a failure you have not seen (a target system may accept bad input). Give the step a way out (`NOK` with a remark) and name the open question.
- No credentials, keys or personal data in the plan ([SEC.2](../../../harness/rules/security/sec-2-no-secrets-or-personal-data.md)). Use roles and test data.
