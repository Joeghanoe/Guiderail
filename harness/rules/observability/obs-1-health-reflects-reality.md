---
type: Rule
title: "OBS.1 A health check reflects what the service depends on, and unhealthy is not a 200"
description: Health covers the dependencies the service cannot work without, lives in its own endpoint, and reports unhealthy with a failing status code so probes and availability tests notice.
rule_id: OBS.1
principle: /principles/p-08-observable-by-design.md
tags: [observability, health, dotnet]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: major
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
  - id: external-dependencies
    resource: Loop page "IntegrationHub Principles" (IH10); user clarification 2026-10-29
---

# Rule

- The health result covers every dependency the service needs to do its job: the queues it reads and
  writes, the external API it calls, the credentials it uses. Expired credentials are unhealthy, even when
  the external service itself is up.
- An unhealthy result returns a status code outside 200-399. Availability tests and load balancers only look
  at the status code.
- The check adds no permission that the service does not need for its real work.
- External systems are checked too. A dependency being outside the team's control does not make its
  failure irrelevant: report which capability and, where applicable, which tenant is affected. Use bounded,
  non-destructive probes or recent operational evidence; a check that cannot establish health reports that
  uncertainty rather than assuming success.
- A health endpoint is its own class and file (CODE.5), named for the service it reports on.

# Boundary

A degraded state (one of two queues down) may return 200 with a payload that says degraded, when the
service can still do its main job. The payload says so, and the alert reads the payload.

An external dependency that prevents the microservice from doing its main job makes it unhealthy, even
when another team must fix the dependency. If useful capabilities remain available, report degraded and
identify the unavailable capabilities; a 200 is acceptable only with an explicit alert reading that state.

For a service serving multiple tenants, check tenant-specific external dependencies and expose their
results through tenant-scoped health or capability status and alerts. One tenant's outage must not make
every tenant look down. The aggregate result reports partial impact as degraded while unaffected tenants
remain usable. An outage that prevents the service's main job across tenants is unhealthy. Each alert names
who can act; external dependencies are never silently omitted from monitoring.
