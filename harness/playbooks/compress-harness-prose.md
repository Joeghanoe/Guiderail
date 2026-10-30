---
type: Playbook
title: Compress harness prose without losing reviewer behaviour
description: Shorten rules and playbooks against the eval suite, keeping an edit only when the pass rate holds and no critical scenario regressed.
tags: [harness, context, evals, maintenance]
status: stable
---

# When

- The always-loaded context is at or near its budget (`infra/scripts/check-context-budget.sh` fails, or
  `bundle.py budget` reports a value close to the recorded one) and text has to come out before text goes in.
- A rule or playbook has grown by accretion and reads as if it were written for a human to be persuaded.
- Never because prose is long. Length is not a defect; cost without value is.

Compression is normally a matter of taste, which is why nobody dares: cut the wrong sentence and the
reviewer silently gets worse. This playbook is only usable because the harness has an instrument that makes
the question falsifiable. [`tools/review/eval.py`](/tools/review/eval.py) turns every human-verified example
into scenarios and scores the reviewer without an LLM judge, so a cut can be tried and measured instead of
argued. The rule is therefore: compress, re-run the evals, keep the edit only if the pass rate holds.

# What this applies to, and what it does not

This playbook governs the harness's rules, playbooks and gate registrations: text that is loaded into an
agent's context, where every byte is paid for on every task that loads it and the index-first design exists
precisely so that prose nobody needs is never read. For that reader, a sentence that restates the sentence
above it is not emphasis, it is cost.

It does not govern TeamValue's human-facing documentation. Vegviser's `Writing Style` standard
(`50-standards/documentation/Writing Style.md`) is the authority there, and it asks for well-developed
paragraphs over isolated one-line statements, for why before how, and against excessive bullet lists. That
standard is right for its artifact: a reference architecture or a standard has to leave the reader able to
reconstruct the reasoning, and a reader who cannot do that cannot apply the document to an example it does not
mention. The two do not conflict, because they are not about the same text. Nothing in this playbook licenses
compressing a Vegviser document, an ADR, a principle (which is a pointer to its external authority), or a
example (which is the eval instrument). When the same sentence appears in both kinds of text, the human-facing
copy keeps its reasoning and the agent-facing copy keeps the citation.

Inside the harness, one kind of prose stays discursive on purpose: the `# Boundary` section of a rule. Its
reasoning is what stops a reviewer from applying the rule where a requirement already explains the code, and
the behaviour it protects is exactly what the boundary examples test. Treat a Boundary like an example, not like
prose. `density.py` already refuses to suggest cutting one; do not override it.

# Precondition: a green baseline

A baseline that is not passing is not a baseline. With a failing gate, a flat pass rate after an edit says
nothing, because it was already the floor: there is no signal left to lose.

At the time of writing, [`tools/review/history.jsonl`](/tools/review/history.jsonl) holds one run, from
2026-10-20: `pass_rate: 0.0` over 15 gating scenarios with 3 critical failures. **Compression cannot be
evaluated against that.** Getting to green is its own work - the reviewer, the examples or the engine, not the
prose - and it is a precondition of this playbook, not a step inside it.

So before anything else:

```bash
python3 -I harness/tools/review/eval.py
```

- Gate `pass`, and `scenarios` at or above `min_scenarios` in
  [`thresholds.json`](/tools/review/thresholds.json): continue.
- Gate `fail`, or any critical failure: **stop and say so.** Report the gate line, the critical failures and
  the fact that compression is blocked until the reviewer is green. Do not compress "carefully" instead.

Record the baseline line as `scenarios`, `passed`, `pass_rate` and `critical_failures`, and the always-loaded
sizes from `python3 -I harness/tools/harness/bundle.py budget`. Everything later is compared against these.

# Steps

1. **Record the baseline** as above, on a clean checkout, and write the numbers into the change description.
   A run on a dirty tree is not appended to the history and is not a baseline either.
2. **Pick candidates**, cheapest and safest first:
   ```bash
   python3 -I harness/tools/harness/density.py candidates --top 20
   ```
   Work down the list in the order it prints: risk 1 (a restatement whose definition site keeps the text)
   before risk 2 (copies with no home, or one sentence around two parameters) before anything flagged
   `narrative`. `density.py` finds candidates; it does not decide. Read the passage before you touch it, and
   drop a candidate the moment the text turns out to carry something the signal could not see. A suggestion
   you rejected is worth a line in the report.
3. **Compress one file per edit.** Several files in one edit means a failed eval cannot be attributed.
   Preserve, every time:
   - every rule ID and every citation of one. A shortened restatement keeps the `(CLD.1)` and drops the
     sentence that repeats it.
   - every `# Boundary` section, in full.
   - every concrete example and every code block. The examples' good and bad examples are what the evals score
     against; a rule's example is what makes it applicable.
   - every frontmatter field. `applies_to`, `severity`, `enforced_by` and `principle` are machine input for
     `bundle.py select`, not prose.
   Then check the cheap things before spending model calls:
   ```bash
   python3 -I harness/tools/harness/bundle.py check    # frontmatter, links and indexes still intact
   ```
4. **Re-run the evals** and compare with the baseline:
   ```bash
   python3 -I harness/tools/review/eval.py
   ```
   Keep the edit only when the pass rate holds at or above the baseline **and** no critical scenario
   regressed. `critical_repeats: 3` in `thresholds.json` exists because the reviewer is not deterministic:
   every repeat of a critical scenario has to pass, so a single green run is not evidence. A scenario that
   passed at baseline and fails now is a regression even if the overall rate still clears `min_pass_rate` -
   revert that edit and record what the sentence was protecting.
5. **Record the result** per edit: file, bytes before and after, pass rate before and after, and which
   scenarios moved. When the always-loaded text shrank (`AGENTS.base.md` or the bundle's `index.md`), lower
   the budget in the same commit:
   ```bash
   python3 -I harness/tools/harness/bundle.py budget --update
   infra/scripts/check-context-budget.sh
   ```
   A budget that only ever ratchets up is not a budget. Leave
   [`context-budget.json`](/tools/harness/context-budget.json) alone when only rules or playbooks changed:
   those bytes are not in it, and the saving belongs in the report instead.
6. **Stop** when the pass rate drops, when the remaining candidates are all high-risk (`narrative`,
   `uncovered-by-evals`, or inside a file no example exercises), or when the next candidate is worth fewer bytes
   than the eval run costs. Stopping early with a number is a result; grinding through the tail is not.

# The honest limit

The evals cover the behaviour the examples cover, and nothing else. Most rules in the bundle have no gating
scenario at all - `density.py report` prints the count per rule, and the `evals` column is `0` for most of
them. Cutting text that no example exercises will show a flat pass rate and may still have removed something
that mattered, because nothing in the suite was ever watching it.

So: **a flat pass rate licenses a cut, it does not prove the cut was free.** Text covered by no example is the
most dangerous thing to compress, not the safest. Two consequences:

- When a cut in uncovered text seems worth making, the cheaper move is to write the example first
  (see `templates/example.md`). Then the eval can speak, and the harness keeps the
  precedent whether or not the compression happens.
- A duplicate is the one exception. De-duplicating does not remove the instruction from the bundle, it
  removes a copy; the definition site still carries it, and `bundle.py select` still returns that rule. Its
  safety rests on the link, not on eval coverage. That is why `density.py` ranks duplication first and why
  it is the only class of cut worth making in text the evals do not reach.

# Report

Conclusion first: bytes before and after per file, the baseline and final `pass_rate` and scenario count,
and whether any critical scenario moved. Then the candidates you rejected and why, and the budget line if
you lowered it. Name anything you cut in text no example covers, explicitly, as an accepted risk - that is the
part a human has to decide.
