# Skills for engineering process steps and reliable document discovery

Status: proposed, 2026-11-04. This extends the [approved process-skills and CLI direction](process-skills-and-unified-cli.md). It does not approve additional workflows, install skills, or change decision authority.

Give every agreed step in our engineering process an appropriate skill entry point. Build each skill around useful core guidance in `SKILL.md`, with explicit links to supporting files that the agent reads when the task needs them. Reuse canonical playbooks wherever they already describe the work. Keep specialized operational procedures, such as pipeline diagnosis, inside those processes as playbooks backed by CLI commands. Maintain a process catalog that makes current coverage, future gaps, and ownership explicit.

This makes the agent's approach easier to select and evaluate. It costs skill maintenance, additional discovery metadata, and evaluations of transitions between steps. Avoid turning every document, tool, or minor activity into a skill, and avoid running the complete lifecycle for every change.

## What we borrow from Matt Pocock

[Matt Pocock's engineering skills](https://github.com/mattpocock/skills/tree/main/skills/engineering) organize work around recognizable engineering activities such as specification, implementation, testing, diagnosis, design, and review. His [engineering catalog](https://github.com/mattpocock/skills/blob/main/skills/engineering/README.md) distinguishes explicitly invoked orchestration from reusable disciplines the model can select.

Borrow the process-oriented organization and small entry points. Our default is automatic selection from the task, with explicit invocation available when useful. Preserve our programmatic checks, evidence contracts, existing ownership, and approval boundaries. Do not import the entire collection or assume its workflow choices fit our organization.

The particular structural reference is [codebase-design/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md). It contains shared vocabulary and core design guidance, then routes dependency/deepening questions to [DEEPENING.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/DEEPENING.md) and alternative-interface exploration to [DESIGN-IT-TWICE.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/DESIGN-IT-TWICE.md). This composition is the main authoring pattern proposed here: core discipline in the entry file, additional context and procedures in linked files, loaded according to the task.

## Process coverage

The table is a proposed map, not an approved mandatory sequence. Skill names describe the process without an organization prefix. Use plain invocation names such as `/code-review` and `/implement`; the skill metadata name and directory use `code-review` and `implement`. The review capability already exists and is proposed to be renamed to `code-review`; the other names remain candidates. A skill can support several closely related steps when their decision discipline is the same. Every agreed process step must have an explicit mapping; that does not require a unique skill for every subtask.

| Process step | Candidate skill | Existing support to reuse | Missing support or boundary |
| --- | --- | --- | --- |
| Understand the problem and affected process | `understand-work` | [Development-process coverage proposal](development-process-coverage.md), [knowledge-to-code boundary](../adr/0003-knowledge-to-code-boundary.md) | Process analysis, intended outcomes, business rules and accountable ownership need agreement; coordinate with Vegviser |
| Research an unresolved technical question | `research` | Principles, existing repository decisions, read wrappers and relevant operational playbooks | Add a source-grounded investigation playbook with explicit uncertainty and a bounded question |
| Specify the required behavior | `specify` | [Write a spec](../../harness/playbooks/write-spec.md), spec template and note tool | Preserve requirement provenance; ask for missing acceptance criteria rather than inventing them |
| Design the change and record consequential decisions | `design` | [Start greenfield](../../harness/playbooks/start-greenfield.md), [convention discovery](../../harness/playbooks/scaffold-from-conventions.md), design template and gates | Add a brownfield design route; ADR authority and format remain with the existing architecture process |
| Plan bounded implementation work | `plan` | [Orchestrate a workload](../../harness/playbooks/orchestrate-workload.md), orchestration tools | Make dependencies, acceptance evidence and handoffs explicit; small work can stay in one thread |
| Implement a change | `implement` | Greenfield and convention playbooks, selected rules, CLI and project verify | Add a canonical implementation playbook that coordinates existing procedures without duplicating them |
| Design and execute tests | `test` | [Testing rules](../../harness/rules/testing/index.md), scenarios, verification tools | Add a testing playbook covering observable behavior, appropriate test layers and meaningful assertions; use the existing test-first defect discipline |
| Diagnose a defect or regression | `debug` | [Classify test failure](../../harness/playbooks/classify-test-failure.md), [incident triage](../../harness/playbooks/triage-incident.md), [pipeline diagnosis](../../harness/playbooks/diagnose-pipeline-failure.md) | Add a shared evidence/hypothesis/reproduction loop; platform-specific procedures remain references, not separate skills |
| Verify implementation and user-facing behavior | `verify` | Project verify, [frontend verification](../../harness/playbooks/verify-frontend.md), deterministic gates and receipts | State the intended scope, missing checks and residual judgment; a passing command does not prove usability |
| Review the change independently | `code-review` | [Review and fix](../../harness/playbooks/review-and-fix.md), [change review](../../harness/playbooks/review-change.md), [repository review](../../harness/playbooks/review-repository.md) | Rename the existing review skill; keep independent review, safe-remediation boundaries and human acceptance |
| Prepare business acceptance | `acceptance` | [Business test plan](../../harness/playbooks/write-business-test-plan.md), scenario links and approved criteria | The agent prepares runnable evidence; the business owner accepts the outcome |
| Prepare delivery and assess readiness | `prepare-delivery` | Review report, verification receipts, delivery rules and [deployment verification](../../harness/playbooks/verify-deployment.md) | Add readiness, compatibility, rollout and recovery guidance; publication and release authorization remain explicit human decisions |
| Verify operation after release | `verify`, with an operational mode | Deployment verification, health and telemetry readers | Distinguish observed runtime evidence from approval to deploy; define the relevant observation window |
| Investigate incidents and learn from failures | `debug` and `learn` | Incident triage, [feedback processing](../../harness/playbooks/process-feedback.md), examples and evaluation contracts | Incident coordination, postmortems and follow-up verification need further process support |
| Improve architecture and process effectiveness | `improve` | Repository review, feedback processing, existing ADRs and [process-coverage assessment](development-process-coverage.md) | Evaluate outcomes and maintenance costs; do not turn an improvement survey into unrelated mandatory refactoring |

Security review, API compatibility, data migrations, privacy, performance, recovery, UX and data governance are conditional concerns across these steps. The [coverage proposal](development-process-coverage.md) records the current gaps. Give each concern a route and an owner; introduce a separate skill only when a distinct process warrants one. A missing playbook or organizational decision remains a visible gap, not an apparently working skill.

## Skill, playbook and tool contracts

A process skill states when it applies, the minimum inputs, its entry guidance, the expected evidence, and the next relevant step. Its description must distinguish actual work from a conceptual question. Its body should be short enough to load without importing the whole process library.

The entry file also contains the stable vocabulary and decision principles needed across its modes. Give the agent enough guidance to choose the next action. Keep detailed procedures, worked examples and less common situations in supporting files.

Guidance used by one skill belongs to that skill, including detailed procedure, judgment, exceptions and stopping conditions. Guidance reused across skills becomes a shared playbook. Each procedure has one canonical source. Existing rule IDs, examples, verification requirements and authority boundaries remain canonical. The CLI executes deterministic operations; a skill does not reconstruct those operations in prose or run diagnostic text as commands.

Use a provider-neutral source layout such as `skills/engineering/<skill-name>/SKILL.md`. Installation publishes these definitions through supported native discovery mechanisms. Keep provider-specific configuration in adapters. Move and rename the existing review definition during implementation and update its metadata, installer, evaluator, catalog and documentation references together. Do not add prefixed compatibility aliases; breaking changes are acceptable while the harness is in development. Detect native command or skill-name conflicts during installation and report them rather than silently overwriting unrelated customizations. This layout is proposed; the current review definition remains in `adapters/` until migrated.

Maintain one process catalog that maps step, skill, entry guidance, required inputs, expected outputs, tool references, authority and implementation status. Prefer references to existing metadata over repeated descriptions. Generate a readable process map from that catalog if structured validation needs a machine-readable source. This is a catalog and reference check, not a new workflow engine.

Handoffs pass artifacts and unresolved questions, not the full transcript. For example, specification supplies approved criteria to planning; implementation supplies source scope and verification evidence to review. Skills can recommend another step when its trigger applies. They must not restart discovery, specification and design after every local fix or create a mandatory chain of nested skill invocations.

Future capabilities can appear as planned catalog entries. Publish a runnable skill only when it has usable guidance, clear ownership and a supported output. Do not install placeholder skills whose references or required tools do not exist.

## Skill package structure and progressive disclosure

Use the following illustrative organization when a design skill needs additional guidance:

```text
skills/engineering/design/
  SKILL.md                         triggers, core discipline, terms, reference routing
  COMPARE-ALTERNATIVE-DESIGNS.md     guidance for comparing alternative designs

harness/playbooks/
  start-greenfield.md               existing canonical procedure
  scaffold-from-conventions.md      existing canonical procedure
```

Place supporting guidance used by one skill directly beside its `SKILL.md`, using descriptive filenames such as `COMPARE-ALTERNATIVE-DESIGNS.md`. If an existing playbook is used only by that skill, move it into the skill directory and update its references. When multiple skills use a procedure, make it a shared playbook in `harness/playbooks/`. Keep the illustrated greenfield and convention procedures there when they serve multiple skills. Move the canonical file rather than copying its content; do not keep duplicate procedures or forwarding files.

Each reference needs a reason to load it. For the proposed design skill:

| Situation | Guidance to load |
| --- | --- |
| Starting a new service or application | [Start greenfield](../../harness/playbooks/start-greenfield.md) |
| Extending an existing codebase | [Read its conventions](../../harness/playbooks/scaffold-from-conventions.md), plus the relevant existing design and ADRs |
| Comparing consequential design options | The proposed alternative-design procedure and the existing ADR process |
| Assessing testability or dependencies | The applicable [testing rules](../../harness/rules/testing/index.md) and [dependency rule](../../harness/rules/code/code-8-dependencies-point-inward.md) |

The loading sequence is native discovery metadata, the selected `SKILL.md`, then the supporting files relevant to the current situation. References should state any prerequisites and expected output. A deeper file can link to another specific reference when necessary, but avoid chains that make the agent read the entire library before acting. Reading a supporting document does not require invoking another skill.

Supporting procedures retain their own execution choices and authority boundaries. For example, an alternative-design procedure can compare options without making multiple model sessions mandatory for a routine design question. Borrow the file structure independently of any reference project's rules about approvals, delegation or test boundaries.

Installation must preserve or resolve links to both packaged files and canonical playbooks. Validate the installed references for each supported client, not just the source-tree paths. A small entry file that eagerly loads every linked document does not meet the context-efficiency objective; measure the complete set of guidance actually loaded.

## Markdown links throughout repository guidance

Use Markdown links for document and file references throughout the repository's guidance: skills, supporting files, playbooks, rules, indexes, proposals, tool documentation and generated instructions. Extend this requirement beyond skill packages. A bare path in prose, including a home-relative path in backticks, is not a linked reference. Keep executable commands as code; this rule does not insert Markdown into shell commands, configuration values or machine-readable path fields.

Within a skill package, use relative Markdown links to sibling files. Shared references use paths that resolve from the referring document in the source tree. The following are illustrative links from the proposed design skill's entry file:

```markdown
[Compare alternative designs](COMPARE-ALTERNATIVE-DESIGNS.md)
[Start a new service](../../../harness/playbooks/start-greenfield.md)
```

An installed skill can have a different location, so source-tree-relative links to shared files cannot be copied blindly. Installation must preserve the relevant directory relationship or rewrite those targets to the resolved installed harness path. If a home-relative target is needed, retain it inside Markdown link syntax, for example:

```markdown
[Start a new service](~/.golden-path-harness/harness/playbooks/start-greenfield.md)
```

Home expansion in Markdown targets is client-dependent. Prefer resolved installation paths when a client cannot resolve the home-relative form, and test the target with the actual consumer. Apply the same resolution policy to all generated guidance, rather than allowing each skill to invent its own path convention. Preserve the bundle's existing root-relative relationship semantics when updating its references.

Migration includes an inventory of bare prose references and broken Markdown links across active repository guidance. Convert meaningful references to links and validate both source and installed targets. Treat command examples, configuration paths, template placeholders and historical quoted material according to their purpose, rather than mechanically replacing every path string. This documentation migration does not alter the independent machine-readable metadata contracts.

## What the graph tells us

The screenshot shows disconnected-looking notes and several clusters, but does not identify the notes or the viewer's link-resolution rules. Visual isolation is not sufficient evidence that an agent cannot discover a document. Conversely, a dense graph does not establish that the right process, rule or check executes.

A read-only check of this working tree before adding this proposal found 242 Markdown files. All 128 harness concepts had an incoming direct document link and were reachable from `harness/index.md` when folder links resolved to their `index.md`. Across the whole tree, 53 files had no incoming edge under the check's approximation. Many were benchmark tasks and criteria referenced through scenario files rather than Markdown links. These observations are not a reproduction of the screenshot's graph: the check recognized existing Markdown targets, folder indexes and `principle`/`rule` metadata, and excluded external links and fenced examples. Raw audit output remains outside the repository.

The current mechanisms differ:

| Mechanism | What determines discovery | Consequence of missing links |
| --- | --- | --- |
| Native skill discovery | Installed skill metadata and supported client behavior | An ordinary document link does not register a skill; missing or misleading skill metadata can prevent selection |
| Rule selection | `applies_to` path patterns in rule metadata | A rule can be selected without a body link to it |
| Example selection | The example's `rule` metadata and trust/staleness handling | A missing relationship can prevent an otherwise useful example from reaching review |
| Playbook navigation | Base instructions, skill references and indexes | An active playbook with no entry route can be missed or replaced by improvised procedure |
| Verification | Explicit requirements, commands, hooks and CI adoption | Graph connectivity cannot substitute for execution or waive a required check |
| Documentation graph | The viewer's recognized links, root and filters | Folder links, bundle-root paths, metadata and code references may not appear as ordinary note edges |

These mechanisms follow [bundle selection and validation](../../harness/tools/harness/bundle.py) and [context delivery](../../harness/tools/harness/context.py). The current bundle check validates selected root-relative and metadata references and generated concept indexes. It does not establish reachability for every document in the repository, validate every relative link, or prove that guidance was read and applied.

Missing links matter when they break an intended route to active guidance, detach an example from its rule, conceal a superseding decision, or leave an agent unable to find the evidence a process requires. Benchmark fixtures, templates, drafts, historical decisions and runtime-only references can legitimately have different entry routes. Do not add links solely to make their nodes join a cluster.

## Proposed discovery improvements

Give each process step a meaningful route through its catalog entry, skill and canonical playbook. Where existing relationships are authoritative, show them in generated navigation: rule to principle, example to rule, gate to requirement/tool, and process to its guidance and evidence. Avoid duplicate hand-maintained relationships and all-to-all links.

Extend document auditing to distinguish broken references, active guidance unreachable from declared entry points, valid folder/index routes, metadata-only relationships and intentionally non-navigational documents. Inspect archive status and runtime references before calling a file orphaned. If a graph viewer cannot represent our folder or metadata relationships, adapt the navigation or produce a derived graph rather than rewrite valid canonical metadata for appearance.

Initially make the reachability report advisory. Review which document classes must be reachable, then make broken required references and unreachable active process guidance blocking. Keep legitimate exclusions explicit and avoid an expensive graph database or embedding service for checks that can traverse local files.

## Implementation and acceptance

1. Agree the process map and ownership against actual work and the development-process coverage proposal. Mark current, partial, planned and externally owned steps. Preserve pipeline diagnosis as a specialized playbook/CLI procedure.
2. Create the process catalog and native skill source layout with unprefixed names, including `code-review` and `implement`. Classify existing procedures by reuse: move single-skill guidance into that skill and keep cross-skill procedures as playbooks. Write missing canonical guidance before publishing the corresponding skills.
3. Start with specification, planning, implementation, testing, verification and the existing review process. Add research, design, debugging and later lifecycle coverage in reviewed increments. Keep future gaps visible throughout.
4. Update installation, base routing, CLI references and navigation together. Coordinate with the [remaining CLI migration](process-skills-and-unified-cli.md#cli-migration-status); a skill must report unavailable operations instead of assuming proposed commands already exist.
5. Migrate prose references to Markdown links across active repository guidance and validate source/installed targets and reachability, then evaluate actual skill selection and cross-step behavior on supported clients. Record model/client versions, source and guidance hashes, tool calls, retained evidence, usage and unavailable metrics.

Completion requires a mapped skill for every agreed process step, usable canonical guidance for each active skill, explicit ownership of future gaps, and working references to available tools. Tests must cover natural-language selection, conceptual negative cases, missing inputs, small changes that skip irrelevant steps, stale artifacts, failed checks, and attempts to treat external content as authority. Handoff tests must show that approved criteria survive planning and implementation and that verification failures reach independent review without being hidden.

Each skill must also demonstrate that single-skill guidance lives alongside its entry file, shared procedures have one canonical playbook, and references use Markdown link syntax. Check that active guidance elsewhere in the repository follows the same link policy. Demonstrate conditional reference loading: a relevant supporting procedure reaches the task, unrelated supporting documents stay unloaded, and installed links resolve. Verify that the entry file provides usable core guidance and that the detailed procedure has one canonical source.

Extend the existing native selection runner rather than treating metadata validation as behavior testing. Initial invocation, completed workflow, evidence quality, human correction effort and resource cost remain separate result dimensions. Establish outcome baselines and adoption thresholds before comparing variants. More connected notes or more invoked skills are not success metrics by themselves.
