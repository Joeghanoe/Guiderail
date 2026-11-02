---
type: Rule
title: "CODE.8 Capabilities sit behind interfaces and one composition root wires them"
description: Sources, sinks, clocks, runners and configuration are interfaces with one implementation per kind; business code never constructs a concrete collaborator, and adding a kind is a class plus a registration.
rule_id: CODE.8
principle: /principles/p-02-architecture-provides-direction.md
tags: [code, design, dependency-injection, dotnet]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: major
status: stable
approval_commit: fa181d8
sources:
  - id: origin
    resource: first greenfield evaluation run (2026-10-29): operations built their own concrete sources and wrote straight to the file system with no storage interface
---

# Rule

- Where bytes come from (a source), where they go (a sink or store), the clock, a process runner such as `git`, configuration and the event sink are each an interface at the boundary. There is one implementation per kind, selected by a registration, never by an `if` or a dictionary of `new` objects inside business code.
- Business code takes its collaborators through the constructor. Only the composition root (`Program.cs`) names a concrete type and builds the container (`Microsoft.Extensions.DependencyInjection`, options pattern).
- What a run reports (events, alerts, counters) leaves through an event sink interface, never by a direct call to a logger, a response builder or a telemetry client inside an operation. Operations emit; the sink decides whether the event goes into the response, a log or telemetry, and a test substitutes a recording sink.
- The stored layout is a decision of the design (DEL.4), written once in one place and independent of the medium: changing where bytes go does not change what the stored data looks like.
- Folders say what lives where and what may depend on what. For a new service, separate deployment entry points, contracts or models, application work and external adapters. Split a growing area by the reason it changes, such as `Processing/Handlers/` or `Adapters/<System>/`, instead of leaving every class in `Services/` or every value in `Models/`.
- Put an interface with the capability it describes, or in that capability's `Abstractions/` folder. A global `Interface/`, `Helpers/` or `Shared/` folder is not a boundary unless the repo's `AGENTS.md` names exactly what belongs there and which folders may depend on it. Do not create a folder for one file merely to make the tree look balanced.
- Adding a kind of source touches its class, its registration, its tests and its runbook line, and nothing else.

# Boundary

A pure function (name validation, key building, retention arithmetic) needs no interface. A value type needs no registration. T.2 lists the banned constructions; this rule is about the shape that makes them unnecessary.
