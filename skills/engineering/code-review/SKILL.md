---
name: code-review
description: Review changes since a fixed point along two parallel axes — Standards (repo standards + Fowler smell baseline) and Spec (originating issue/spec requirements). Use when reviewing a branch, PR, or diff.
---

# Two-Axis Code Review Discipline

Review code along two independent axes without letting one mask the other.

## 1. Pin the Fixed Point
- Compare against merge-base: `git diff <fixed-point>...HEAD`.
- Confirm ref resolves (`git rev-parse <fixed-point>`) and diff is non-empty before proceeding.
- Pre-flight quality gate: run `tvh verify --repo .`. If verification fails, stop and report failures first.

## 2. Axis 1: Standards (Repo Rules + Smell Baseline)
Evaluate whether the diff conforms to repository conventions and architectural hygiene.
- **Documented Repo Standards**: Check against TeamValue rules (`CODE.*`, `SEC.*`, `T.*`, etc.) via `tvh review --repo . --baseline <fixed-point>`.
- **Fowler Smell Baseline** (heuristic judgment calls, subordinate to repo standards):
  - *Mysterious Name*: name doesn't reveal intent or purpose.
  - *Duplicated Code*: same logic shape across multiple hunks.
  - *Feature Envy*: method reaches into another object's data more than its own.
  - *Data Clumps*: parameters or fields that always travel together without a dedicated type.
  - *Primitive Obsession*: primitive types used where a domain value object belongs.
  - *Repeated Switches*: conditional cascades on types recurring across the diff.
  - *Shotgun Surgery*: one conceptual change forces edits across scattered files.
  - *Divergent Change*: single module edited for multiple unrelated reasons.
  - *Speculative Generality*: hooks, parameters, or abstractions not demanded by the spec.
  - *Message Chains*: deep `a.b().c().d()` coupling.
  - *Middle Man*: delegating without adding behavior.
  - *Refused Bequest*: inheriting or overriding while ignoring parent contracts.
*(Skip anything linters or compilers already enforce).*

## 3. Axis 2: Spec (Requirement Conformance)
Evaluate whether the diff faithfully satisfies the originating requirements:
- Missing or partial requirements requested by the spec/work item.
- Scope creep: behavior in the diff not requested by the spec.
- Incorrect behavior: implemented logic that conflicts with acceptance criteria.

## 4. Reporting & Aggregation
Present findings under `## Standards` and `## Spec` side by side.
- **Do not rerank across axes**: a change can pass Standards but fail Spec, or pass Spec while failing Standards.
- End with a summary of the worst issue within each axis.
- The agent never approves a PR; merge decisions remain with human reviewers (CLD.2).
