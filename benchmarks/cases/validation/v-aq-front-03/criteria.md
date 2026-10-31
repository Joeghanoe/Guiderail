# Criteria v-aq-front-03 (hidden from the candidate)

Functional
- G01 The value is read from the snapshot as delivered; no domain logic or recomputation in the frontend (the portal takes severity from the backend).
- G02 "complete" renders nothing new; "partial" and "failed" render one indicator on the health page, distinguishable from each other by text or icon and not by colour alone.
- G03 The indicator is exposed to assistive technology (role status or an accessible name), keyboard reachable if interactive, and passes a contrast check in the light and the dark theme.
- G04 Operators get a short statement of what is affected or what to do next; customers get neutral wording without internal terms; no tagline or text that explains the screen or the product.
- G05 Historical snapshots show the quality of the snapshot being viewed, not of the live one.
- G06 The placeholder snapshot used while loading does not flash the indicator.
- G07 Unit tests for each state and for the two roles; the existing tests still pass.

Rules checked: UI.1 (the candidate looks at the built screen: a screenshot per state, taken with the repo's screenshot tool, and a contrast check), UI.2 (every element earns its place; no explanatory copy), CODE.5 (the indicator is its own component in its own file; the page does not grow another responsibility), T.2, T.5.

Hard gates
- Screenshots of complete, partial and failed exist in the PR evidence (UI.1).
- No explanatory text about the screen, the product or the legend (UI.2).

Regressions
- Changing the legend, the canvas engine or the polling interval.
- Colour as the only signal.
- Adding a dependency for an icon the project already has.
