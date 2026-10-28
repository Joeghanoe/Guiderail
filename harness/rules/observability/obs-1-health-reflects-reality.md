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
---

# Rule

- The health result covers every dependency the service needs to do its job: the queues it reads and
  writes, the external API it calls, the credentials it uses. Expired credentials are unhealthy, even when
  the external service itself is up.
- An unhealthy result returns a status code outside 200-399. Availability tests and load balancers only look
  at the status code.
- The check adds no permission that the service does not need for its real work.
- A health endpoint is its own class and file (CODE.5), named for the service it reports on.

# Boundary

A degraded state (one of two queues down) may return 200 with a payload that says degraded, when the
service can still do its main job. The payload says so, and the alert reads the payload.

A dependency the service does not own and cannot fix, such as a customer's tenant or one partner's API in
a service that serves many, stays out of the health result: one party's outage must not make the service
look down for every party. It is covered by an alert per party (OBS.2) that names who has to act. The
dependencies the service owns, including its own credentials and the stores every party needs, stay in.
