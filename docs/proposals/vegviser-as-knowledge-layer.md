# Proposal: Vegviser is the knowledge, the harness only routes and enforces

Status: **proposed**, for discussion. Nothing in the harness changes until a human accepts it.
Date: 2026-10-25.

## Decision asked

Make Vegviser, reached through its MCP server, the only place where TeamValue's way of working is written
down: principles, rules, cases and playbooks. The harness keeps only what has to run on a machine or in a
pipeline (hooks, read wrappers, gates, the review and its evals) and a short routing table for the two
groups that use it: **developers** and the **triage department**.

Assumption from the request: the Vegviser MCP is always available. There is no offline copy and no
fallback.

## Why

- **The same rule lives in two places and drifts.** CLD.2 was narrowed in Vegviser (PR #300) and needed a
  second change here. Until both landed, the hook contradicted the rule.
- **The harness already defers to Vegviser.** `principles/` holds 14 files that only point to Vegviser at a
  pinned commit. Rules, cases and playbooks are the same kind of knowledge, kept in a second format.
- **Colleagues outside development already ask Vegviser.** The M365 Copilot agent uses the same MCP. A rule
  that a developer's agent reads should be the rule a consultant or a triage colleague is told.
- **Thin is cheaper.** Today `harness/` holds about 3,600 lines of knowledge (principles, rules, cases,
  playbooks) next to about 3,800 lines of executable tools and hooks. Only the second part needs a local
  install.

## Target shape

### What stays in the harness

| Part | Why it stays |
|---|---|
| `AGENTS.base.md`, cut to about 30 lines: the five hard rules as one line each, how to reach Vegviser, and the routing table | Hard rules must be in context before any tool call, and must not depend on retrieval (see *Security*) |
| `hooks/` (guard-bash, guard-read, stop-verify) | They run on the machine, before a tool call |
| `tools/` read wrappers: cloud, sonar, servicenow, azure-devops | They run under the user's own identity; an MCP server cannot do that |
| `tools/review/` (`review.sh`, `eval.py`, `thresholds.json`, `render.py`) and `pipelines/ai-review.yml` | The review and its gate run in the pipeline |
| `tools/testing/` (`check-scenarios.py`, `business-testplan.py`), `tools/diagrams/` | Executable generators and gates |
| `gates/` registrations | They describe this repo's checks; their rule IDs point to Vegviser |
| `templates/finding.md`, `templates/repo/`, `adapters/`, `install.sh`, `tests/` | Output schema, repo starter kit, tool wiring, tests |
| `router.md`, new | Developer and triage routing (below) |

### What moves to Vegviser

| Part | Vegviser destination | Note |
|---|---|---|
| `rules/` (40 files) | An SDLC rule catalog under Governed SDLC Engineering Standards: one entry per rule ID, with text, `applies_to` globs, severity and `enforced_by` | The two-layer form (architecture basis, Microsoft route) is added where a rule is more than a one-liner |
| `cases/` (19 verified, plus drafts) | Precedent cases next to the rule catalog | They stay project-agnostic; `project-terms.txt` moves with them |
| Playbook method: triage, verify a deployment, diagnose a pipeline, classify a test failure, business test plan, add an example, process feedback | The playbooks named in Vegviser KS-0104 (HL-1, HL-2, HL-3) and the feedback route | The tool-specific commands stay here, in `router.md` |
| `templates/case.md`, `templates/business-testplan.spec.json` | Vegviser templates | |

### What is deleted

`principles/` (pointers only), `index.md` files for moved folders, and the parts of `bundle.py` that check,
index and select local knowledge (`index`, `check`, `select`, `check-case`, `submit-feedback`).
`privacy-check` and `findings` stay.

## Routing

`router.md` maps what a person asks to two things: the Vegviser authority that says *what to do and why*,
and the harness tool that does the read. The agent reads the authority through the MCP and runs the tool
locally. The current table in `AGENTS.base.md` ("When the user says … You have …") becomes this file.

### Developers

| When a developer says | Vegviser (MCP) | Harness tool |
|---|---|---|
| "review this" / "is this ready" | Rules selected for the changed paths; review method | `verify.sh`, `check-scenarios.py`, `review.sh`, `render.py` |
| "the pipeline failed" | Pipeline diagnosis and its cause classes | `ado-run-failure.sh`, `ado-run-watch.sh` |
| "a test fails" | Test-failure classification | none; the repo's test runner |
| "did the deploy work" | Post-deployment verification | `cloud-read.sh` |
| "check Sonar" | Quality-gate rule | `sonar-read.sh` |
| "add this as an example" | Case template and feedback route | `/example` adapter |
| "how do we do X here" | `consult_vegviser`, audience `engineer` | none |

### Triage department

| When triage says | Vegviser (MCP) | Harness tool |
|---|---|---|
| "something is broken" / "errors in prod" | Incident triage: evidence order, cause classes (deploy, configuration, dependency, capacity, data), handoffs | `cloud-read.sh` (health, App Insights, resource state), `ado-run-failure.sh` for a deploy cause |
| "why does ServiceNow do X" | Read-only SaaS configuration analysis | `sn-get.sh`, `sn-access-check.sh` |
| "was this caused by a release" | Deployment verification and pipeline diagnosis | `ado-run-watch.sh`, `cloud-read.sh` |
| "is there a known fix" | Not Vegviser: solution articles stay in the ITSM tool | An ITSM article read wrapper, still an idea (`feedback/grounded-incident-triage-from-knowledge-base.md`) |

For both groups, the agent **classifies** the cause and a **human confirms** it before anyone acts. Every
state change is written down as a command for a human (CLD.2).

A triage colleague who works only in M365 Copilot gets the Vegviser knowledge but not the live evidence: the
read wrappers need a shell and the user's identity. Live triage therefore needs the same install as a
developer (`install.sh`, read-only cloud login).

## How it works

**In a session.** The agent loads `AGENTS.base.md` (hard rules, router). For a task it follows the router
entry: it asks the MCP for the authority and runs the local tool. The selection that `bundle.py select` does
today becomes one MCP call per task, so the context stays small without a local bundle.

**In the PR pipeline.** `review.sh` sends the changed paths to the MCP and receives the rules and cases
that apply. This must be **deterministic**: the same paths and the same Vegviser version return the same
rules. Ranked question answering (`consult_vegviser`) does not guarantee that, for the same reason Vegviser
added `list_vegviser_capabilities`. See *What Vegviser has to add*.

**Pinning.** Today the pipeline pins a harness commit. After the change it pins two things: the harness
commit (tools) and the Vegviser publication version (knowledge). The receipt records both, plus the rule
IDs and the version each was served at.

**Evals.** `eval.py` keeps building throwaway repos and scoring without a model. It fetches the cases for a
pinned Vegviser version instead of reading `cases/`. Masking the case under test still happens, on the
fetched set. Accepting a case in Vegviser extends the regression set, as it does now.

## What Vegviser has to add

The harness change depends on these. Each goes through Vegviser's own pipeline and PR route.

1. **Rule catalog** with stable IDs, version, `applies_to` globs, severity and `enforced_by`. Today CLD.2
   is a bullet inside a capability document.
2. **Deterministic read tools** on the MCP server, read-only like the existing two:
   - `select_vegviser_rules(changed_paths, publication)` returns rules and cases for those paths;
   - `get_vegviser_rule(rule_id, publication)` and `get_vegviser_document(path, publication)` return one
     item by identity;
   - every response carries the publication version it was served from.
3. **An audience value for triage**, for example `operations`, next to `engineer`.
4. **A workload identity for the PR pipeline** that can call the MCP and nothing else. The review job has
   no service connection today. That stays true for cloud resources; this identity reaches only Vegviser.
5. **Intake for harness feedback.** Corrections from `/example` become Vegviser practice evidence or
   rule-change proposals, through the Knowledge Processing Pipeline.

## Security

- **Hard rules stay local.** SEC.1, SEC.2, CLD.1, CLD.2 and H.1 remain in `AGENTS.base.md` and in the
  hooks. Content returned by the MCP can add detail and can make the agent more careful. It cannot widen
  what the agent may do: the hooks and the identity decide that, not retrieved text.
- **Retrieved content is data (SEC.1).** A Vegviser document that says "skip this check" is treated like
  any other untrusted text. The MCP contract already requires this on the server side (MCP-07).
- **No new write path.** The MCP stays read-only. All writing tools stay local, under the user's identity
  and the hooks.

## Feedback after the change

| Feedback | Goes to |
|---|---|
| A rule is wrong, unclear or does not fit (a boundary) | Vegviser: rule-catalog change or boundary case |
| A hook, wrapper or gate behaves wrongly | Harness PR |
| A repeated task (H.2) | Method to Vegviser; script or hook to the harness |
| A triage cause that keeps coming back | Vegviser practice evidence; the structural fix in the product repo |

H.1 still holds, and stays local: an agent proposes a case and does not edit rules. The case now lands in
Vegviser.

## Steps

| Step | Done when |
|---|---|
| 1. Vegviser adds the rule catalog and the deterministic tools | `select_vegviser_rules` returns the same set as `bundle.py select` for the test paths in `tests/run.sh` |
| 2. Parallel run | The PR pipeline selects locally and through the MCP, records both in the receipt, and fails on a difference. Run until 20 PRs show no difference |
| 3. Evals on Vegviser cases | `eval.py` against the pinned publication passes `thresholds.json`, with the same scores as the local cases |
| 4. Router replaces local knowledge | `router.md` in place; `AGENTS.base.md` cut down; the developer and triage routes each tried on one real task |
| 5. Delete moved folders | `rules/`, `cases/`, `principles/`, moved playbooks and the local-knowledge parts of `bundle.py` removed; `tests/run.sh` updated |

Every step can be reverted on its own until step 5.

## Measures

- Rule drift between a hook and its rule: zero, checked in CI by comparing each hook's rule ID and version
  with what the MCP serves.
- Reviewer eval pass rate: unchanged or better against `thresholds.json`.
- Context per task: the tokens loaded for a review, before and after.
- Size of `harness/`: knowledge files go to zero; what remains is tools, hooks and the router.

## Open questions for a human

1. Is one rule catalog under Governed SDLC Engineering Standards the right home, or should the rules sit in
   the existing Vegviser standards (Security, Engineering, Observability)?
2. Who owns the rule catalog in Vegviser, and does a rule change need the harness owner's review because a
   hook may enforce it?
3. Does the triage department work in a CLI agent with the harness installed, or only in M365 Copilot? That
   decides whether live triage is in scope for them.
4. Do the playbook commands stay in `router.md`, or does Vegviser hold a Microsoft route per playbook that
   names the harness tools?
5. Who owns the PR pipeline's MCP identity, and where is it reviewed?

## Out of scope

- Changes to the MCP server's existing tools or hosting.
- Solution articles of the triage department; they stay in the ITSM tool.
- Customer-specific rules; they stay in each repo's `AGENTS.md`.
