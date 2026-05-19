---
name: Frontend State And Data
id: frontend-state-and-data
description: Frontend state management and async data-loading patterns for TeamValue UI.
applyTo: '**/*.ts,**/*.tsx'
---

Use this skill for stores, hooks, query behavior, redirects, and async page states.

## State patterns

- Place cross-cutting state in stores, not scattered local state.
- useEffect is disallowed by default.
- Do not use useEffect for derived state, prop-to-state syncing, event logic, or parent notifications.
- Prefer render-time derivation and memoization (useMemo) over effect-driven state updates.
- Prefer event handlers for user-triggered logic (POSTs, notifications, multi-state updates).
- Prefer resetting component trees with a key instead of effect-based resets.
- Prefer useSyncExternalStore for external subscriptions instead of manual effect subscriptions.
- If unsure, prefer event-driven flows over lifecycle-driven flows.

## Allowed exceptions for useEffect

- Synchronizing with external systems that React does not control (browser APIs, non-React widgets, imperative integrations).
- Data fetching in hooks when required by the architecture, with cleanup/ignore logic to prevent race conditions.
- App-visibility logic that must run because the component is displayed, not because of a user event.
- Every exception must include a short justification comment near the effect.

## Data and routing behavior

- Put server data fetching in hooks with centralized query keys.
- Gate protected routes and privileged queries by role checks before requesting protected data.
- Handle redirect flows explicitly with a redirect-in-flight error pattern instead of silent retries.
- Render explicit loading and error states for all async pages. No silent fallbacks.

## Review checks

- Are there any useEffect calls without a valid exception and local justification?
- Is state centralized where shared and local where isolated?
- Are protected requests role-gated before query execution?
- Are redirect, loading, and error states explicit (POLA)?
