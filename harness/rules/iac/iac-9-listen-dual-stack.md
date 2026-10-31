---
type: Rule
title: "IAC.9 A service listens on both IP families, and its probe uses the loopback address"
description: Services bind to the dual-stack wildcard so they are reachable on an IPv6-only private network, and container health probes call 127.0.0.1, not localhost.
rule_id: IAC.9
principle: [/principles/p-06-automation-by-default.md, /principles/p-08-observable-by-design.md]
tags: [iac, networking, containers, health]
applies_to: ["**/*.cs", "**/*.json", "**/*.yml", "**/*.yaml", "**/*.conf", "**/*.template", "**/Dockerfile*", "**/*.sh"]
enforced_by: [gate:/gates/dual-stack.md, review]
severity: major
status: draft
sources:
  - id: origin
    resource: FoodApp portal build (2026-10-31): the plan warned that Railway's private network is IPv6-only, yet the Directus container's health check failed because localhost resolved to ::1 while Directus listened on IPv4 only. Found only by running the compose stack.
---

# Rule

- A service that other services reach over a private network binds to the dual-stack wildcard, not to `0.0.0.0` alone, which is IPv4
  only and unreachable on an IPv6-only network (Railway's private network, some Kubernetes clusters):

  | Stack | Dual-stack form |
  |---|---|
  | ASP.NET (Kestrel) | `http://[::]:$PORT` (or `http://+:$PORT`), never `http://0.0.0.0:$PORT` |
  | nginx | `listen PORT;` and `listen [::]:PORT;` |
  | Node | `server.listen(port, '::')` |
  | Python (uvicorn, gunicorn) | `--host ::` / `-b [::]:PORT` |
  | Directus and other `HOST` settings | `HOST=::` |

- A container health probe calls `127.0.0.1`, not `localhost`. `localhost` can resolve to `::1` first and fail against a listener that is
  IPv4 only (or the other way round); `127.0.0.1` reaches both a `0.0.0.0` and a `::` listener on Linux.
- The check is local: bring the container up and let its health check pass. A probe that never ran green proves nothing.

# Boundary

A service that is deliberately reachable only on one family (a sidecar on loopback, a database that the platform fronts) says so on the
line with `dual-stack: ok` and a reason.

# Check

`tools/iac/check-dual-stack.py` (gate `dual-stack`) finds the wildcard IPv4 binds and `localhost` probes above; review covers what it
cannot see (a bind set in code from a variable, a platform default).
