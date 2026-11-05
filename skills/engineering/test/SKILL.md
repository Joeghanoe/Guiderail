---
name: test
description: Design, write, and execute tests following strict TDD discipline and TeamValue testing rules. Use when writing unit tests, integration scenarios, or designing test suites.
---

# Testing & TDD Discipline

Write meaningful, falsifiable tests that protect business invariants and verify real public behavior.

## Core Rules & The Red-Green Loop
1. **Red Before Green**: Write a failing test exercising the intended behavior before writing any production code.
2. **Minimal Code to Pass**: Write only the code required to make the failing test pass. Avoid anticipatory code.
3. **Confirm the Public Seam**: Before writing a test, state the public boundary/interface you are exercising. Test against public behavior, not private implementation details.
4. **Test in the Right Layer (T.3)**: Unit tests for domain logic; integration tests for DB/API contracts; smoke tests for deployments.

## Anti-Patterns to Guard Against
- **Implementation-Coupled Tests**: Tests that mirror private methods or internal state, breaking whenever code is refactored without behavioral change.
- **Tautological Assertions**: Tests that mirror or duplicate the implementation logic rather than asserting against an independent source of truth.
- **Horizontal Slicing**: Writing all tests across a technical layer at once. Prefer vertical slices through a feature seam.

## Process & Tooling
Follow the [Testing Rules](~/.golden-path-harness/harness/rules/testing/index.md) (`T.1`–`T.6`):
1. Write the failing test at the confirmed seam.
2. Run test presence check:
   `tvh checks test-presence`
3. Verify scenario mapping (T.5):
   `tvh checks scenarios --input-file <changed.txt>`
4. Run tests locally via repo runner (`dotnet test`, `pnpm test`) to confirm green.

## Expected Evidence
A failing test reproducing a defect (for fixes) or a clean green suite verifying new behavior along a confirmed public seam.
