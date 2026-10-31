---
type: Gate
title: "Dual-stack check (IAC.9)"
description: check-dual-stack.py fails a PR that binds a service to the IPv4 wildcard only or probes a container through localhost.
tool: harness/tools/iac/check-dual-stack.py
owner: team:teamvalue-aicoe
status: draft
tags: [iac, networking, containers]
---

# Coverage

Source and config files (`.cs`, `.json`, `.yml`, `.yaml`, `.conf`, `.template`, `.sh`, `Dockerfile*`), one finding per line: a Kestrel,
Node, Python or `HOST` bind to `0.0.0.0` without a `::` form, an nginx file that listens on IPv4 only, and a container health probe that
calls `localhost`.

# Blind spots

A bind that comes from a variable or the platform default; a probe written in a language the script does not read; whether the service
should be reachable on both families at all (review, and `dual-stack: ok` with a reason marks a deliberate exception).

# Complementary checks

Starting the container and letting its health check go green. AI review of IAC.9.

# Failure behaviour

Exit 1 with `path:line: IAC.9 message`; the PR step fails.

# Exception route

`dual-stack: ok - <reason>` on the same line.

# Refresh trigger

A new server stack in a repo, or a change to IAC.9.
