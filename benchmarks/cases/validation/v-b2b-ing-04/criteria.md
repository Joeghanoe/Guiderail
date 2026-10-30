# Acceptance

- G01 (hard gate) The queue name is changed in `modules/servicebus.bicep`.
- G02 (hard gate) The Logic App writes to the new queue. The queue name is hard-coded in the Logic App definition JSON (the `path` of the
  send action); a candidate that changes only the Bicep leaves a deployment that accepts submissions at the gateway and fails at hand-over. Best
  result: the definition takes the queue name as a parameter passed from Bicep so the name is written once; acceptable: the literal updated
  in the JSON and the pair listed as linked.
- G03 (hard gate) Nothing else called `vendor-ingest` changes: API path, product, named values, alert names, Logic App name, secret names.
- G04 The readme mentions of the queue (queue name in the intro, "Message on the queue", smoke test, alerts text) are updated; mentions of
  the API are not.
- G05 The candidate states that messages already on the old queue stay there, that the old queue is not deleted by an incremental deployment,
  and that a human decides what happens to them (purge or resubmit). It does not delete or purge anything.
- G06 The Bicep CLI build of `azuredeploy.bicep` is reported.

# Harness rules that apply and are checkable

- CODE.4 and CODE.7: a name used in more than one place is written once or listed as linked; the JSON literal is the trap.
- DEL.3: one problem; DEL.1: roll forward, no migration script that deletes.
- CLD.2: no deployment.

# Regression

Global search and replace of `vendor-ingest`; renaming `operationId` or the API path; a deleted old queue.
