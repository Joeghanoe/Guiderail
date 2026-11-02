# Orchestration Tools

Tools for decomposing complex workloads across specialized subagent teams and routing tasks to cost-effective model tiers.

Playbook: [orchestrate-workload.md](../../playbooks/orchestrate-workload.md).

## Tools

* `orchestrate.py` - Evaluates task complexity, recommends cost-effective model tiers (`economy`, `builder`, `reasoner`), and generates multi-agent work package decomposition plans; `orchestrate.py layers` counts the layers a task or a change touches and exits 3 when three or more need a plan and the report holds neither the plan nor a stated reason for one thread.

## Model Tiers

| Tier | Focus | Token Weight / Cost |
|---|---|---|
| **Economy** | Linting, formatting, regex rules, boilerplate, translation check | ~0.1x - 0.25x |
| **Builder** | Feature implementation, component views, API endpoints, unit tests, Bicep modules | ~1.0x |
| **Reasoner** | Architecture design, security/auth, lead review, conflict resolution | ~3.0x - 5.0x |

## Model names

The tool is vendor-neutral: it speaks in tiers and takes names from configuration, with no provider as the default.

* `models.json` (this folder) - the names the harness can vouch for, each provider with the date they were checked.
* `~/.config/harness/models.json` - yours; add any vendor. A provider here replaces the same provider above, whole.
* `--models FILE` - one-off, same format.

```json
{ "providers": { "my-vendor": { "reviewed": "2026-10-28", "economy": "...", "builder": "...", "reasoner": "..." } } }
```

Choose with `--provider my-vendor` or `HARNESS_MODEL_PROVIDER=my-vendor`. Without either, `plan` lists tiers only and
`tier` lists every configured provider's name. A provider that is not configured is an error: a name is never guessed.
