# Rules

* [OBS.1 A health check reflects what the service depends on, and unhealthy is not a 200](obs-1-health-reflects-reality.md) - Health covers the dependencies the service cannot work without, lives in its own endpoint, and reports unhealthy with a failing status code so probes and availability tests notice.
* [OBS.2 An alert follows causality: it fires when something breaks, and when the proof that it works is missing](obs-2-alerts-follow-causality.md) - An alert is true when the thing works and silent only then; no data, a stopped signal or a check that cannot run counts as broken, not as healthy.
* [OBS.3 Operational output is a contract: named events, stable codes, identifiers instead of content](obs-3-operational-output-is-a-contract.md) - What a run reports is a fixed set of events and fields with stable names and error codes, carries run and source identifiers and counts, and never payloads, names of customer data or credentials.
