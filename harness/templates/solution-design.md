---
type: Template
title: Solution design
description: Skeleton for docs/solution-design.md of a new repo or service (DEL.4); every heading is answered, or says why it does not apply.
tags: [design, architecture, greenfield]
status: draft
---

# <Service name>: solution design

One paragraph: who uses it and why it exists. Then the question that drives every decision:

> <the one question this service answers, answerable with yes or no and a named reason>

## Scope

| In | Out |
|---|---|
| <what it does> | <what someone will read into it and it does not do> |

## Components

A diagram (Mermaid) and a table: component, responsibility, depends on (interfaces only, CODE.8). Say which
parts are real here and which are stand-ins (a local folder for a bucket) and why the stand-in is safe. For each
adapter, name the test that runs it against the real dependency or a recorded real response (T.6).

## Data flow and stored layout

How data gets in, where it is stored and the exact key or path layout. State what is fixed before the first
write and why. Say what one stored unit contains, so that it can be restored alone. Link the ADR.

## Expected size and cost

For each collection a component loops over: the expected size, the largest size the spec or data allows, the algorithm
shape chosen for that largest size (CODE.9), what a search does when it hits a limit (inconclusive, never a negative
answer), and the scale test that runs at ten times the expected size with its time budget.

## Identity of a run, and repeating it

How a run is named, what a second call with the same name does, and how two runs are kept apart.

## Failure model

What a partial failure looks like, what stays healthy, what is reported, which reason codes exist (OBS.3),
what is never silent (corrupt or missing data on read), and what is never overwritten.

## Observability contract

Events, properties, status and health calls (OBS.1, OBS.3), and what is never recorded (SEC.2).

## Retention and lifecycle

What is kept how long, from when, who or what deletes, and how the rule is tested with a controlled clock.

## Security and isolation

What input is never trusted (paths, locations, identities), what the service may touch, what it must never modify.

## Decisions

| ADR | Decision | Why it is hard to reverse |
|---|---|---|

## Known limits

What is not verified and what would change the design.
