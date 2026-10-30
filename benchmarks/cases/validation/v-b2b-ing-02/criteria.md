# Acceptance

- G01 (hard gate) A new alert resource exists in `modules/monitoring.bicep`, enabled only through the existing `alertingEnabled` parameter
  (`enabled: alertingEnabled`), and it notifies the existing action group. No second action group, no new e-mail address, no literal address.
- G02 (hard gate) The alert name follows the existing pattern `${prefix}-vendor-ingest-alr-<what>` and is declared as a variable next to the others.
- G03 (hard gate) The readme "Alerts" table has a row for the new alert with when it fires and its severity.
- G04 Severity is informational (3) or at most 2 with a stated reason: a 429 means the limit worked, not that a submission was lost.
- G05 The criteria scope to the vendor-ingest API (the `apiName` dimension), not the whole gateway.
- G06 The Bicep CLI build of `modules/monitoring.bicep` succeeds (candidate reports the command and its output).
- G07 The change needs no new parameter in `azuredeploy.bicep`, or, if it adds one, it is passed from there and has a default.

# Harness rules that apply and are checkable

- OBS.2: the alert has a cause (429 count over a window) and an `autoMitigate` choice that matches it.
- IAC.6: resource and variable names follow the repo's own naming.
- IAC.1: no new diagnostic or log category is turned on to feed the alert.
- CODE.7: bicep and readme change together.
- T.1: the candidate reports what it ran (the build) and what it could not (a deployment).

# Regression

Alert enabled in every environment; hard-coded recipient; alert on all 4xx (noise); changing the existing three alerts.
