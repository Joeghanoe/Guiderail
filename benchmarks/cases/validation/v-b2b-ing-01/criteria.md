# Acceptance

- G01 (hard gate) The operation policy accepts media type `text/csv`, case-insensitively and with a `; charset=...` suffix, and still refuses everything outside the list with 415.
- G02 (hard gate) The OpenAPI request body lists `text/csv`, so the contract given to vendors and the policy agree.
- G03 (hard gate) The readme table row for 415 and the text of the 415 error message in the policy list the same set of types.
- G04 The 200 KB limit, the 400 and 413 behaviour and the list of forwarded headers are unchanged.
- G05 No wildcard or "any text/*" match is introduced.
- G06 The candidate says what it did not run: the policy has no local test harness, so it names the smoke test (readme, "After the first deployment") the human has to run after deployment.

# Harness rules that apply and are checkable

- CODE.7: the places that list media types (policy condition, policy error text, OpenAPI, readme) change together; a miss is a finding.
- CODE.4: the candidate does not invent another copy of the list.
- DEL.3: one problem, no drive-by edits in the other policy sections.

# Regression

Removing or renaming an existing media type; changing a status code; touching `operationId` `submit` (renaming breaks deployment); deploying or pushing (CLD.2).
