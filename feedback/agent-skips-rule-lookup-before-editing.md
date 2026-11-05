---
type: Example
title: "C-NNN The agent edits config without reading the rules and examples that apply to it"
description: A pre-edit lookup that is only an instruction gets skipped; a hook that gates the first edit and surfaces the linked examples makes it reliable.
example_id: C-NNN
rule: /rules/harness/h-2-repeated-work-moves-up.md
verdict: automation-candidate
status: draft
tags: [feedback, harness, hooks, pipelines]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-01T21:00:00Z }
sources:
  - id: evidence
    resource: a session refactoring Azure Pipelines YAML and Bicep across eight deploy pipelines
---

# Situation

The global instructions say: before editing code, open [index.md](../harness/index.md), run `bundle.py select --brief <files>` and open the rule files whose summary applies. In a session that refactored eight pipelines into one shared deploy template, the agent did none of it and edited Bicep and YAML directly. The result broke IAC.7 and its newer examples (E-044, E-049): the new template forwarded about 30 values as template parameters, kept fixed values as parameter defaults, and left the environment catalog as a top-level pipeline parameter. The owner noticed and asked why the example had not been applied.

Two causes. The lookup is an instruction, and instructions get skipped under momentum. And when it does run, `select --brief` prints one line per rule. The examples that carry the newer convention are linked from the rule body, two hops away, so even a run that follows the instruction does not put them in front of the agent.

# Why (verdict)

H.2 says a check that guards a rule moves up the ladder from instruction to hook. The lookup guards every rule, so it is the clearest candidate. Fix the setup before relying on memory or on stronger wording.

# Proposed change (for the harness repo; agents do not edit it, H.1)

1. **Edit gate.** A `PreToolUse` hook on `Edit|Write` (and `NotebookEdit`) denies the call until `bundle.py select` has run in this session. `select` writes a marker keyed by the session id. The denial message names the command to run, so the agent recovers in one step.
2. **Surface the examples.** On the first edit of each file type per session, the hook returns `additionalContext`: the matching rule summaries plus the titles and paths of the examples linked from those rules, with human-verified, newer examples first. For `*.yml` that includes IAC.7, E-006, E-044 and E-049. `select --brief` gains an `--examples` line per rule for the same purpose.
3. **Backstop.** [stop-verify.sh](../harness/hooks/stop-verify.sh) fails the turn when code files changed and no `select` marker exists, so a miss is caught even where the edit hook did not run (for example in CI or Copilot).
4. **Prose last.** A repo `AGENTS.md` may name the rules that matter most there (here: IAC.7, with E-044 as the target layout). That supplements the hook; it does not replace it.

Not a rule change: IAC.7 and E-044 were right. The proposal changes how they reach the agent.

# Compliant pattern

## Good example

```text
agent: Edit Pipelines/deploy-connector.yml
hook:  denied (H.2 edit gate). Run: bundle.py select --brief Pipelines/deploy-connector.yml
agent: bundle.py select --brief Pipelines/deploy-connector.yml
select: IAC.7 ... examples: E-044 (pipeline inputs are run choices), E-049 (nested templates read $(var))
agent: Edit Pipelines/deploy-connector.yml   # now reads $(name) variables from variables files
hook:  allowed
```

## Bad example

```text
agent: Edit Pipelines/deploy-connector.yml   # no lookup; instruction skipped
# no gate, no examples in context; ~30 forwarded template parameters ship
```

# Not verified

Drafted from one session by the agent that made the mistake. Steps 1 and 2 are now prototyped: [edit-gate.sh](../harness/hooks/edit-gate.sh) (PreToolUse on `Edit|Write|NotebookEdit`), a session marker written by [guard-bash.sh](../harness/hooks/guard-bash.sh) when it sees `bundle.py select`, and `select --brief --examples`. Tested in [run.sh](../tests/run.sh) (edit-gate section) with Claude Code's hook input. The marker lives under `$TMPDIR/golden-path-harness-lookup/<session_id>`; it fails open when there is no `session_id` or no [bundle.py](../harness/tools/harness/bundle.py). Not yet checked in Copilot or CI, and the [stop-verify.sh](../harness/hooks/stop-verify.sh) backstop (step 3) is not built. It does not contradict a human-reviewed example.
