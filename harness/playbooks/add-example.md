---
type: Playbook
title: Add an example case
description: Turn real code that follows or breaks a rule into a case with a concrete good and bad example.
tags: [harness, cases, examples]
status: stable
---

# When

- A user runs `/example` (Claude Code or Copilot), with or without a pointer to code.
- You come across code that clearly follows or breaks a rule. Then propose it in your summary
  ("candidate example for T.2: ..."); write the case only when the user agrees or runs `/example`.

# Project-agnostic, always

A case teaches a way of working that holds in any TeamValue repo. It is not the record of one project's
design decision.

- No customer, partner, product, project or system names. Use neutral names: `Contoso`, `PartnerService`,
  `OrderStore`, `partner.example.com`.
- Only the lines that show the pattern: one class, one method, no domain detail the rule does not need.
- A design decision for one project ("we chose X for this customer") belongs in that project's ADR or
  exception record, not in the harness.

**Challenge project-specific input.** When what the user offers is specific to a project, say so, name what
makes it specific, and propose the generalized version: the rule, a neutral snippet, the verdict. Write the
case only after the user agrees with that version. If it cannot be generalized without losing its point, it
is a design decision: suggest an ADR in the repo and stop.

# Steps

1. **Pick the rule.** Find it through `~/.harness/index.md`. No rule fits: say so and stop; an example without a
   rule is an opinion.
2. **Check for a requirement first.** Code that looks like a violation can be what was asked for: an
   interface per customer because the contract demands it, a key because the partner offers nothing else.
   Look for the requirement (work item, ADR, contract, the repo's `AGENTS.md`) and ask the user if you cannot
   find it. A stated requirement makes the verdict `boundary`, never a `violation`. A boundary case follows
   Vegviser's Exception and Risk Acceptance playbook in short: a `requirement` source that names the *kind*
   of requirement ("a contract that requires a separate interface per customer"), an `owner` (`human:<id>`)
   who accepted the pattern, and a `stale_after` date when it must be reviewed again. The project's own
   exception record stays in that project. After `stale_after` the reviewer stops treating it as precedent.
3. **Start from real code, then generalize it.** Take the smallest snippet that shows the problem, rename
   everything project-specific to neutral names, and strip what the rule does not need. Keep the structure
   that shows the pattern. Secrets and personal data never appear, not even renamed (SEC.2). The original
   location may go in `sources` as internal provenance; it is optional.
4. **Take the good example from real code when it exists**, in this or another TeamValue repo, with its source.
   Otherwise write the smallest version of the bad snippet that follows the rule, and label it
   "written for this example".
5. **Both snippets solve the same problem**, so the reader sees the difference and nothing else. Describe
   the way of working ("storage clients authenticate with managed identity"), not the story of one change
   ("storage switched to a connection string"). The good example shows the practice itself, not something
   that merely hides it. Set `example_file` when the rule depends on where the code lives (`src/Program.cs`).
   An accepted case is also an eval: its bad example must be flagged by its rule, its good one must not.
6. **Write the case** from `~/.harness/templates/case.md` into `~/.harness-feedback/`, named
   `<rule-id>-<slug>.md` (`t-2-httpclient-in-partner-service.md`). Keep `case_id: C-NNN`; the harness repo
   numbers it when a human accepts it. `status: draft`, `generated` with your actor, no `verified`.
7. **Check it.** `python3 ~/.harness/tools/harness/bundle.py check-case ~/.harness-feedback/<file>.md`, run from the repo you are in, must pass: a
   `violation`, `compliant` or `boundary` case needs `## Good example` and `## Bad example`, each followed by a
   code block, and may not contain a name from `templates/project-terms.txt` or the current repo's name.
   The check catches known names only; you are responsible for the rest.
8. **Report** the rule, the verdict and the file. A human verifies it and moves it into the harness repo
   (`harness/cases/`), adding `verified: { by: human:<id>, at: ... }`.

# Verdicts

| Verdict | Use when |
|---|---|
| violation | The code breaks the rule and no requirement explains it |
| compliant | The code follows the rule in a way worth copying |
| boundary | The rule does not apply here, and the case says why (often a requirement) |
| rejected | Feedback against a rule that the harness keeps; the case records why |
| open | The verdict needs a human decision; the case states the question |
| automation-candidate | A repeated task that should become a playbook, script or check (H.2) |
