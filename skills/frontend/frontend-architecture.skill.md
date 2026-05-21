---
name: frontend-architecture
description: Frontend architecture and composition constraints for TeamValue TypeScript/React work.
---

Use this skill for component boundaries, UI composition, and frontend architectural consistency.

## Architecture principles

- **A.3** - One framework per frontend domain. Do not mix UI libraries.
- **A.12** - Each component has a single, clear responsibility.
- **A.19** - Shared functionality is reused at design time, not runtime.
- **POLA** - User-facing behavior must be predictable and consistent.

## Composition conventions

- Use kebab-case for component, page, hook, store, and utility filenames.
- Keep components functional and focused.
- Never edit generated UI components directly; compose from them.
- Reuse shared logic via shared packages at design time, not runtime service calls.

## Review checks

- Is the component single-responsibility (**A.12**)?
- Is composition used instead of editing generated components (**A.19**)?
- Does the UI behavior remain predictable (POLA)?
