---
name: typescript
description: TeamValue TypeScript conventions — strict typing, kebab-case filenames, framework version n-1, no implicit any.
---

You are writing or reviewing TypeScript. Follow these conventions to keep code type-safe, predictable, and consistent with the rest of the TeamValue frontend. For component composition see [[frontend-architecture]]; for stores and async data see [[frontend-state-data]]; for client-side security see [[frontend-security]].

## Tooling and versioning

- Target framework and runtime at **n-1** (current stable minus one) per global defaults.
- Compile under `strict: true`. Do not weaken individual strict flags to silence errors.
- Keep `noImplicitAny`, `strictNullChecks`, and `noUncheckedIndexedAccess` on.
- Treat type errors and lint errors as build failures, not warnings.
- Format with the project formatter (Prettier) — never hand-format to fight it.

## Typing discipline

- **No implicit `any`.** If a type is genuinely unknown, use `unknown` and narrow before use.
- Never use `// @ts-ignore`. Use `// @ts-expect-error` with a short reason when a suppression is truly unavoidable.
- Avoid `as` casts. Prefer type guards, narrowing, and discriminated unions. A cast needs a justification comment.
- Do not use the non-null assertion `!` to paper over nullability — handle the null case.
- Prefer `type` aliases for unions and composition; use `interface` for object/contract shapes meant to be extended or implemented.
- Make illegal states unrepresentable: model variants as discriminated unions rather than optional-field soup.
- Derive types from data (`typeof`, `keyof`, `ReturnType`, `as const`) instead of restating them.

## Naming and files

- **kebab-case** for all filenames — components, pages, hooks, stores, utilities, types.
- PascalCase for types, interfaces, enums, and React components.
- camelCase for variables, functions, and parameters; `UPPER_SNAKE_CASE` only for true module-level constants.
- Name booleans as predicates (`isLoading`, `hasAccess`, `canEdit`).
- One clear responsibility per module (**A.12**); reuse shared logic at design time, not runtime (**A.19**).

## Functions and data

- Annotate exported function signatures explicitly; let inference handle locals.
- Prefer pure functions and immutable data. Use `readonly` and `as const`; avoid in-place mutation of inputs.
- Use early returns to reduce nesting; keep functions short and single-purpose.
- Prefer `unknown`-typed `catch` and narrow the error before reading it.
- Use `async/await` consistently; never leave a promise unawaited (no floating promises).

## Boundaries and safety

- Validate all external input (API responses, params, env, storage) at the boundary — do not trust declared types from outside the app. Parse into typed shapes (e.g. a schema validator) before use.
- Never expose secrets or sensitive fields in client-visible types, state, or payloads (**S.3**).
- Fail securely — do not leak sensitive data through error types, messages, or logs (**S.6**).
- No PII in logs.

## Anti-patterns (avoid)

- `any`, blanket `as` casts, `!` assertions, and `@ts-ignore`.
- Enums of strings where a `const` object + union would be clearer and safer.
- Re-declaring types that can be derived from existing ones.
- Optional fields used to encode mutually exclusive states.
- Swallowing errors or returning silent fallbacks instead of explicit states.

## Review checks

- Does it compile under `strict` with no suppressions or implicit `any`?
- Are casts and assertions absent or individually justified?
- Are external inputs validated at the boundary before being treated as typed?
- Are filenames kebab-case and types PascalCase?
- Are illegal states unrepresentable rather than guarded by convention?
- Are secrets excluded from client-visible types and outputs (**S.3**, **S.6**)?
