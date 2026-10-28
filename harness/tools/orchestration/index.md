# Orchestration Tools

Tools for decomposing complex workloads across specialized subagent teams and routing tasks to cost-effective model tiers.

Playbook: [orchestrate-workload.md](../../playbooks/orchestrate-workload.md).

## Tools

* `orchestrate.py` - Evaluates task complexity, recommends cost-effective model tiers (`economy`, `builder`, `reasoner`), and generates multi-agent work package decomposition plans.

## Model Tiers

| Tier | Focus | Token Weight / Cost | Example Models |
|---|---|---|---|
| **Economy** | Linting, formatting, regex rules, boilerplate, translation check | ~0.1x - 0.25x | Gemini Flash Lite, Claude Haiku, GPT-4o-mini |
| **Builder** | Feature implementation, component views, API endpoints, unit tests, Bicep modules | ~1.0x | Gemini Flash, Claude Sonnet, GPT-4o |
| **Reasoner** | Architecture design, security/auth, lead review, conflict resolution | ~3.0x - 5.0x | Gemini Pro, Claude Opus, o1 |
