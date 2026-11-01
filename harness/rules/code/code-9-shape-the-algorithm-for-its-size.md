---
type: Rule
title: "CODE.9 State the input size a component must handle, and shape its algorithm for that size"
description: A design states the expected and maximum size of each collection a component loops over; the algorithm is chosen for that bound, a search that hits a limit says inconclusive and not infeasible, and one test runs at ten times the expected size with a time budget.
rule_id: CODE.9
principle: [/principles/p-02-architecture-provides-direction.md, /principles/p-08-observable-by-design.md]
tags: [code, design, performance, scale, search]
applies_to: ["**/*.cs", "**/*.ts", "**/*.py"]
enforced_by: [review]
severity: major
status: draft
sources:
  - id: origin
    resource: FoodApp comparison (2026-10-31): the same menu solver built design-first with the harness (71 tests, all at 7 to 8 recipes per meal type) took 31 s and wrongly answered "not enough distinct days" at 30 recipes per type, where the iterative build planned the week in 60 ms. The cause was two choices that no rule asked anyone to make explicit.
---

# Rule

1. **Size is a design decision.** The solution design (DEL.4) names, for each collection a component loops over, the expected size and the largest size the spec or the data allows (recipes in a library, rows in an import, items in a queue). If the spec is silent, write down the assumption and the reason. A component is not finished against an unstated size.
2. **Shape for the bound, once, at design time.** Pick the algorithm whose cost fits the stated maximum. Three shapes fail quietly because they pass on small data:
   - materialising a full product of collections (nested loops that build every combination, then filter or sort);
   - sorting or scanning everything to pick a few, when the pick can be made while searching;
   - one call to a store or service per item inside a loop (N+1) when one call can fetch the set.

   Where a search is needed, prune on a bound that is cheap to compute (a total that can no longer be reached) before enumerating, so the work follows the answer and not the product of the inputs.

3. **This is not micro-optimisation.** Shape is chosen by reasoning about the stated size. Constants, caching, parallelism, allocation tuning and clever data structures wait for a measurement that shows a need.
4. **A cutoff is not a verdict.** A limit on a search (branch cap, node budget, timeout, row cap) can only produce "inconclusive" or "truncated", reported as such. It never produces the negative answer ("infeasible", "none found", "no match"), because the caller would act on a claim the code did not establish. Either the search is exact, or the result carries that it was cut off.
5. **One test at ten times the expected size.** The component has a layer 0 or 1 test (T.3) that runs at ten times the expected size, or at the stated maximum if that is larger, with ties and identical values in the data (they defeat ordering shortcuts), and asserts both the answer and a time budget generous enough for a CI machine (seconds, not milliseconds). The size and the budget are named in the design.

# Boundary

Code that loops over a fixed small set (the four meal types, the seven days, a list of ten settings) needs none of this. A one-off script, a migration run once, and a prototype whose design says "prototype, sizes unknown" are exempt until they are promoted. This rule does not ask for benchmarks, profiling in CI or a performance budget for every function.

# Check

Review reads the design for the size statement, reads each loop over a stated-large collection for the three shapes in point 2, reads each limit for what it returns when hit, and finds the scale test. Missing size statement, a limit that returns a negative verdict, or no scale test at a stated size is a major finding that cites CODE.9. A design-gate check for the size heading is a candidate (`design-check.py`) once the heading has been in use for a few runs.
