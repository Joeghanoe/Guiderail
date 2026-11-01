---
type: Rule
title: "UI.1 A visual change is looked at, at every screen size, before it is called done"
description: A change to something users see is rendered, screenshotted at phone, tablet and desktop widths, checked for WCAG 2.2 AA, and judged against the people who will use it.
rule_id: UI.1
principle: [/principles/p-01-business-before-technology.md, /principles/p-06-automation-by-default.md]
tags: [frontend, accessibility, responsive, wcag, ux]
applies_to: ["**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte", "**/*.razor", "**/*.cshtml", "**/*.html", "**/*.css", "**/*.scss"]
enforced_by: [review]
severity: major
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T20:11:03Z }
sources:
  - id: origin
    resource: FoodApp prototype, "Frontend Visual Verification Rule" in its AGENTS.md, generalized
---

# Rule

A change that alters what a user sees is run and looked at before it is reported done (T.1 for the visual part). `playbooks/verify-frontend.md` is the how; `tools/frontend/screenshot.mjs` is the tool.

- **Rendered, not assumed.** The page runs and is screenshotted at 320 (reflow), 390 (phone), 768 (tablet) and 1280 (desktop) CSS pixels. The agent opens the screenshots and looks at them; a passing build says nothing about layout.
- **Responsive.** No horizontal scroll at 320 px, nothing cut off or overlapping, touch targets of at least 44x44 px on phones (24x24 px is the WCAG 2.2 AA floor), text readable without zoom.
- **WCAG 2.2 AA.** Contrast 4.5:1 for text and 3:1 for large text and controls, every control has an accessible name and a label, images have `alt`, one `h1` and a `main` landmark, `lang` is set, focus is visible and the page works with the keyboard alone. The tool checks what a machine can check; the rest the agent checks by reading the screenshots and the markup.
- **Fit for the audience.** The repo's `AGENTS.md` names who uses the screen (role, context, device, skills, language). The agent judges the screenshots against that person: is the main task obvious, is the wording theirs, is the density right? When the repo names no audience, the agent says so and asks instead of inventing one (P1).
- **Reported honestly.** The summary lists the screens and sizes looked at, what the tool found, what the agent saw that a tool cannot, and what was not checked (a state it could not reach, a screen reader it did not run).

# Boundary

- Only visual tools. A change to an API, a job or a library with no UI is out of scope.
- Automated checks cover roughly a third of WCAG; passing them is not conformance. Say so in the report; do not claim "WCAG compliant".
- Screenshots are test data (SEC.2): run against synthetic or seeded data, never a production page with personal data. The tool only opens localhost unless the user allows a remote URL.
- Do not add colours, fonts or radii that the repo's style guide does not have; propose the change instead.
