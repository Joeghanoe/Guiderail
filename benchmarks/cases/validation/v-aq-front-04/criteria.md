# Criteria v-aq-front-04 (hidden from the candidate)

Functional

- G01 The page file keeps composition and state wiring only; the selects, the virtualised rows and any other component each sit in their own file; types and interfaces are not hidden inside component files.
- G02 The pure functions (build editable list, bucketing, filtering, visible buckets, move services, environment detection, comparison helpers) move to a module outside the component tree and each has tests with fixed inputs.
- G03 No behaviour change: same props, same keys in lists, same virtualisation row model, same save payload shape; mutations still invalidate the same query keys.
- G04 Nothing is left behind unused after the move (dead helpers, commented code, unused imports).
- G05 No duplicated helper is introduced next to an existing one in the lib folder (for example resource id parsing is reused).
- G06 The change is one thing: no new feature, no style change, no dependency change, and it lands in reviewable steps or a clearly ordered diff.

Rules checked: CODE.5 (one responsibility, every type in its own file), CODE.1 (remove what is not used), CODE.4 (a repeated expression is written once), T.3 (tests at the right layer), DEL.3.

Hard gates

- Typecheck, lint and unit tests pass (T.1).
- Screenshots of the screen before and after, same data, show no visual change (UI.1 as evidence for a refactor).

Regressions

- Changing behaviour while moving code (for example sort order, default selection, debounce).
- A new shared "utils" file that collects unrelated helpers.
