# Criteria (hidden from the candidate)

## Functional
- G01 (hard gate) A new alert rule fires when no `...Completed` event (the success event, name in the connector
  telemetry: `<Operation>Completed`) has been recorded within a window longer than the schedule (for a nightly job,
  about 26 hours). The query must produce a row when the table has no rows at all (e.g. a datatable-based left
  join or a count-with-zero pattern), because an empty result is the failure being detected.
- G02 (hard gate) The existing failure rule is not removed or weakened.
- G03 The new rule reuses `Modules/scheduled-queryrule.bicep` and is deployed by the same pipeline task, with
  parameters that follow the module's style. The evaluation window and frequency suit a nightly job (not 5 minutes).
- G04 The candidate explains the two cases: Started but not Completed or Failed (hung), and nothing at all.
  Either both are covered or the gap is named.
- G05 The window is tied to the schedule in a comment or parameter; changing the schedule changes the alert in
  one place or the link is stated.
- G06 The candidate does not run `az`; hands over the `bicep build` and what-if commands, and says it did not
  execute the query against a workspace.
- G07 The alert tells the reader which of the two things happened (no data vs failed) in its description or
  dimensions.

## Rule IDs checkable
OBS.2 (absence of signal is an alert), IAC.1 (diagnostics proportionate), CODE.7 (the event name used in the
query also exists in the connector code and is listed), CODE.4 (event name written once as a parameter),
CLD.1, CLD.2.

## Regression
- A rule that only counts Completed events with `threshold 0` and treats zero rows as healthy.
- A 5-minute window with an hourly job (flapping).
- Alert enabled flag hard-coded differently from the existing rule.
- Pipeline task added but the template parameter list not matching.
