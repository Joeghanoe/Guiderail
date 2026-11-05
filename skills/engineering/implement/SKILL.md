---
name: implement
description: Implement code changes, features, or bugfixes following vertical slicing, test-first discipline, and TeamValue coding rules. Use when writing, modifying, or refactoring code.
---

# Implementation Discipline

Deliver clean, maintainable code in vertical slices backed by test evidence and verified against TeamValue standards.

## Core Rules
1. **Vertical Slices**: Implement features as complete, runnable vertical slices through the stack, rather than horizontal layer-by-layer scaffolding.
2. **Minimal Code to Satisfy Spec**: Write only the code required to satisfy the agreed criteria or failing tests. Resist speculative generality.
3. **Single Responsibility (DEL.3)**: A change solves one problem and shows its evidence. Keep PRs small and self-contained.
4. **Zero Secrets (SEC.2)**: Never commit secrets, credentials, or read `.env` files (use `.env.example`).
5. **Done Means Verified (T.1)**: Every new behavior ships with tests that exercise it.

## Process & Tooling
1. Select applicable guidance before editing:
   `tvh context select --brief --changed --baseline <baseline>`
2. Follow discovered repo conventions:
   `tvh scaffold conventions --raw -- --root <repo>`
3. Check code structure and conventions:
   `tvh checks code-types --json -- App.cs`
4. Run project verification before declaring done:
   `tvh verify --repo .`

## Expected Evidence
Working, formatted code accompanied by passing unit/scenario tests and clean verification receipts (`tvh verify`).
