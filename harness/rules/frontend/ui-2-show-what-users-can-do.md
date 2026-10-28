---
type: Rule
title: "UI.2 A screen shows what the user can do, not what the screen is for"
description: Every element on a screen helps the user reach their goal. Text that explains the product, the screen or the spec is removed; headers, footers and cards carry only what the user acts on.
rule_id: UI.2
principle: [/principles/p-01-business-before-technology.md]
tags: [frontend, ux, content, minimalism]
applies_to: ["**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte", "**/*.razor", "**/*.cshtml", "**/*.html", "**/*.css", "**/*.scss"]
enforced_by: [review]
severity: major
status: draft
sources:
  - id: origin
    resource: User feedback on a generated screen whose footer read "replaces the legacy RAG process" and whose header and cards carried badges nobody asked for
---

# Rule

A screen is built from the user's goal, not from the spec. Before designing it, write down who the user is and what
they came to do (from the repo's `AGENTS.md`; ask when it is not there, P1). Every element earns its place by
helping that person reach that goal: by being something they act on, or something they need in order to decide
what to do next. What does not, goes. The spec explains why the screen exists; the user does not need to read that.

- **Never explain the screen.** No taglines, no "replaces the legacy process", no "here you can...", no description of
  what the product does or why it exists. That text belongs in the spec, the README or the ADR.
- **The goal has an obvious way in.** The action that serves the user's main goal is the most prominent thing on the
  screen, easy to find and easy to click, with a label that names the outcome ("Get started", not "Submit"). Other
  actions are visibly quieter, and rare ones are tucked away. When everything is emphasised, nothing is.
- **Navigation is where users expect it.** The places the user goes to are reachable and labelled, not hidden behind
  an icon to guess. The header is for finding your way and for who you are signed in as; anything the user
  uses on content belongs next to that content.
- **The shortest path to the goal.** Ask only what the task needs, prefill what is known, and show where the user is
  in a multi-step flow and how to go back. A form is made clear by its labels, not by instructions above it.
- **Footers are empty unless they serve the user:** legal links or a support contact. A copyright line or slogan
  only when the repo's `AGENTS.md` asks for it.
- **Cards and rows show what the user compares or decides on,** and the action. A chip, percentage or date stays when
  the user chooses differently because of it. When two things say the same, keep one; a summary that restates the
  list below is removed.
- **A message says what happened and what to do, once.** No repeating the title in the body, no technical ids,
  and the actions are the ones that resolve it.
- **Colour, spacing and type carry meaning.** Colour marks what needs attention or action, not decoration; the same
  kind of element looks and is spaced the same everywhere, so the screen reads as one system.
- **One language, the audience's.** Labels, statuses and buttons follow the repo's `AGENTS.md`; no `Submitted` next to
  `Groen`.
- **Empty and error states point to the next action.**
- **Density follows purpose.** A catalogue, dashboard or overview can legitimately show a lot, because browsing and
  comparing is the goal; a task screen (fill in, approve, pick one thing) shows only what that task needs. Judge
  the amount of content against the goal of this screen, never against a fixed number.
- **Test for every element:** "what would this user do differently, or fail to do, if it were gone?" If nothing,
  remove it.

# Boundary

- Required content stays: legal text, accessibility labels, error messages that tell the user how to recover.
  Accessible names are not visible clutter; keep them (UI.1).
- The repo's `AGENTS.md` or the product owner can ask for an element explicitly; then it stays. Do not add it on
  your own because it "fills" the layout. White space is fine.
- Colours, fonts and radii stay with the repo's style guide (UI.1); this rule decides what earns a place on the screen.
- A finding names the element, which goal it does not serve, and what to remove or merge, with the screenshot. It
  does not cite a count.
