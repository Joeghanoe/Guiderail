#!/usr/bin/env python3
"""Workload orchestration and model tiering tool for AI agent teams.

Decomposes complex milestones or multi-faceted tasks into decoupled subagent
work packages, recommends cost-effective model tiers (minimizing token usage
and cost), and validates completion gates.

Commands:
  tier     Evaluate task/diff complexity and recommend model tier and token budget
  plan     Decompose a task/spec into specialized subagent work packages (3-10 workloads)
  verify   Validate that subagent work packages pass their defined test gates
"""

import argparse
import json
import re
import sys

# Model mapping by tier across provider ecosystems
MODEL_TIERS = {
    "economy": {
        "description": "Fast, high-throughput, low-cost for rote tasks, linting, boilerplate, and regex verification",
        "models": {
            "gemini": "gemini-2.0-flash-lite / flash_lite",
            "anthropic": "claude-3-5-haiku / haiku",
            "openai": "gpt-4o-mini",
        },
        "relative_cost": "0.1x - 0.25x",
        "token_budget_typical": "2k - 10k tokens",
    },
    "builder": {
        "description": "Balanced, capable for standard feature development, components, endpoints, and test suites",
        "models": {
            "gemini": "gemini-2.5-flash / flash",
            "anthropic": "claude-3-7-sonnet / sonnet",
            "openai": "gpt-4o",
        },
        "relative_cost": "1.0x",
        "token_budget_typical": "10k - 30k tokens",
    },
    "reasoner": {
        "description": "Deep reasoning, high-context for architecture design, security reviews, lead orchestration",
        "models": {
            "gemini": "gemini-2.5-pro / pro",
            "anthropic": "claude-3-opus / opus",
            "openai": "o1 / o3-mini",
        },
        "relative_cost": "3.0x - 5.0x",
        "token_budget_typical": "20k - 60k tokens",
    },
}

ROTE_KEYWORDS = [
    r"\blint\b",
    r"\bformat\b",
    r"\bprettier\b",
    r"\bboilerplate\b",
    r"\bclean\s*up\b",
    r"\bdelete\b",
    r"\bremove\b",
    r"\brename\b",
    r"\btypes?\s*only\b",
    r"\btranslate\b",
    r"\bi18n\b",
    r"\bregex\b",
    r"\bguardrail\b",
]

REASONER_KEYWORDS = [
    r"\barchitect(ure)?\b",
    r"\bsecurity\b",
    r"\bauth(entication|orization)?\b",
    r"\badr\b",
    r"\bdesign\b",
    r"\breview\b",
    r"\borchestrat(e|ion)\b",
    r"\bdata\s*model\b",
    r"\bcrypt(o|ography)\b",
    r"\bprotocol\b",
    r"\bstrategy\b",
]


def classify_tier(text: str, changed_files: list[str] | None = None) -> dict:
    """Classify the optimal model tier based on task description and affected files."""
    text_lower = text.lower()
    files = changed_files or []

    reasoner_matches = [p for p in REASONER_KEYWORDS if re.search(p, text_lower)]
    rote_matches = [p for p in ROTE_KEYWORDS if re.search(p, text_lower)]

    is_infra = any(f.endswith((".bicep", ".tf", ".yaml", ".yml")) for f in files)
    is_core_domain = any("domain" in f.lower() or "auth" in f.lower() for f in files)
    is_docs = all(f.endswith((".md", ".txt", ".json")) for f in files) if files else False

    if is_docs and not reasoner_matches:
        tier = "economy"
        rationale = "Documentation, configuration, and data-only changes are low complexity."
    elif len(reasoner_matches) >= 2 or (is_core_domain and "auth" in text_lower):
        tier = "reasoner"
        rationale = f"High architectural/security impact detected: {', '.join(reasoner_matches[:3])}."
    elif len(rote_matches) >= 2 and len(reasoner_matches) == 0:
        tier = "economy"
        rationale = f"Maintenance, lint, or mechanical changes detected: {', '.join(rote_matches[:3])}."
    elif is_infra and "refactor" in text_lower:
        tier = "reasoner"
        rationale = "Infrastructure refactoring touches security and blast radius."
    else:
        tier = "builder"
        rationale = "Standard software development task (implementation, tests, endpoints, views)."

    info = MODEL_TIERS[tier]
    return {
        "tier": tier,
        "rationale": rationale,
        "relative_cost": info["relative_cost"],
        "token_budget_typical": info["token_budget_typical"],
        "model_recommendations": info["models"],
    }


def generate_plan(spec_text: str, split_count: int | None = None) -> dict:
    """Decompose a task into discrete, decoupled subagent workloads (flexible 3-10 splits)."""
    text_lower = spec_text.lower()
    packages = []

    # Check if task is exclusively backend or deeply focused
    is_backend_only = (
        any(k in text_lower for k in ["backend", ".net", "c#", "api", "database", "sql", "ef core", "service"])
        and not any(k in text_lower for k in ["frontend", "react", "ui", "view", "css", "html"])
    )

    if is_backend_only or (split_count and split_count >= 5 and "backend" in text_lower):
        # Granular backend decomposition (3-6 workloads for backend alone)
        packages.append({
            "role": "qa-harness-sentinel",
            "title": "Standards & Code Rule Guardrails",
            "tier": "economy",
            "model": MODEL_TIERS["economy"]["models"]["gemini"],
            "deliverables": ["Code style and banned symbol checks", "Negative tests and boundary verification"],
            "verification_command": "scripts/verify.sh --fast || dotnet test",
            "file_boundary": ["tests/**", "Directory.Build.props"],
        })
        packages.append({
            "role": "domain-rules-engineer",
            "title": "Domain Entities & Pure Business Rules",
            "tier": "builder",
            "model": MODEL_TIERS["builder"]["models"]["gemini"],
            "deliverables": ["Domain entities, value objects, and business rules", "Pure domain unit tests"],
            "verification_command": "dotnet test --filter Category=Domain",
            "file_boundary": ["src/**/*.Domain/**", "tests/**/*.Domain.Tests/**"],
        })
        packages.append({
            "role": "persistence-migration-engineer",
            "title": "Database Schema & EF Core Mapping",
            "tier": "builder",
            "model": MODEL_TIERS["builder"]["models"]["gemini"],
            "deliverables": ["DbContext, entity configurations, soft-delete query filters", "Migration scripts"],
            "verification_command": "dotnet test --filter Category=Persistence",
            "file_boundary": ["src/**/*.Infrastructure/**", "src/**/Migrations/**"],
        })
        packages.append({
            "role": "api-controller-engineer",
            "title": "API Endpoints & Middleware",
            "tier": "builder",
            "model": MODEL_TIERS["builder"]["models"]["gemini"],
            "deliverables": ["HTTP endpoints, correlation ID middleware, DTO validation", "Controller tests"],
            "verification_command": "dotnet test --filter Category=Api",
            "file_boundary": ["src/**/*.Api/**", "tests/**/*.Api.Tests/**"],
        })
        packages.append({
            "role": "integration-scenario-sentinel",
            "title": "Integration Scenarios & Health Probes",
            "tier": "builder",
            "model": MODEL_TIERS["builder"]["models"]["gemini"],
            "deliverables": ["End-to-end component tests and boundary scenario verification"],
            "verification_command": "dotnet test --filter Category=Integration",
            "file_boundary": ["tests/**/*.IntegrationTests/**"],
        })
    else:
        # Standard multi-disciplinary or full-stack decomposition
        packages.append({
            "role": "qa-harness-sentinel",
            "title": "Quality Gate & Repository Guardrails",
            "tier": "economy",
            "model": MODEL_TIERS["economy"]["models"]["gemini"],
            "deliverables": ["Automated guardrail test suite", "Linter and formatting alignment", "Illegal stack deprecation"],
            "verification_command": "scripts/verify.sh --fast || pnpm test",
            "file_boundary": ["tests/**", ".gitignore", "scripts/**"],
        })

        if any(k in text_lower for k in ["backend", ".net", "c#", "api", "database", "sql", "ef core", "endpoint"]):
            packages.append({
                "role": "dotnet-backend-builder",
                "title": "Backend Domain & API Implementation",
                "tier": "builder",
                "model": MODEL_TIERS["builder"]["models"]["gemini"],
                "deliverables": ["Domain entities & authorization", "ASP.NET Core API", "xUnit unit & integration tests"],
                "verification_command": "dotnet test",
                "file_boundary": ["src/**/*.cs", "tests/**/*.cs", "*.sln"],
            })

        if any(k in text_lower for k in ["frontend", "react", "ui", "view", "vite", "typescript", "component", "tokens", "i18n"]):
            packages.append({
                "role": "react-frontend-builder",
                "title": "Frontend UI & Component Implementation",
                "tier": "builder",
                "model": MODEL_TIERS["builder"]["models"]["gemini"],
                "deliverables": ["React views & components", "Brand token styles", "i18n localization", "Vitest component tests"],
                "verification_command": "pnpm test || npm test",
                "file_boundary": ["src/**/*.Web/**", "apps/web/**"],
            })

        if any(k in text_lower for k in ["infra", "bicep", "azure", "cloud", "deployment", "sql serverless", "swa"]):
            packages.append({
                "role": "bicep-infra-engineer",
                "title": "Infrastructure as Code & Cloud Modules",
                "tier": "builder",
                "model": MODEL_TIERS["builder"]["models"]["gemini"],
                "deliverables": ["Bicep modules and parameter files", "Zero secrets compliance", "Infra validation tests"],
                "verification_command": "pnpm test tests/infra-rules.test.ts",
                "file_boundary": ["infra/**"],
            })

    # Always present: Lead Orchestrator & Reviewer
    packages.append({
        "role": "lead-orchestrator-reviewer",
        "title": "Lead Review, Integration & Verification Gate",
        "tier": "reasoner",
        "model": MODEL_TIERS["reasoner"]["models"]["gemini"],
        "deliverables": ["Workload assignment matrix", "Integration testing across packages", "Final review receipt"],
        "verification_command": "all verification gates passing",
        "file_boundary": ["*"],
    })

    return {
        "title": f"Workload Orchestration Plan ({len(packages)} work packages)",
        "work_packages": packages,
        "execution_rules": [
            "Local-first execution: keep all changes local; do not push or commit prematurely.",
            "Bounded context: each agent strictly operates within its designated file boundaries.",
            "Deterministic gates: each work package must pass its verification command with 100% success.",
            "Lead review: the orchestrator performs four-eyes review and integration before milestone acceptance.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Workload orchestration and model tiering tool for AI agents.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tier_parser = subparsers.add_parser("tier", help="Classify task/diff complexity and recommend optimal model tier.")
    tier_parser.add_argument("--task", type=str, default="", help="Task or story description.")
    tier_parser.add_argument("--files", nargs="*", default=[], help="List of affected files.")
    tier_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format.")

    plan_parser = subparsers.add_parser("plan", help="Generate a multi-agent work package decomposition.")
    plan_parser.add_argument("--spec", type=str, default="", help="High level specification or backlog item.")
    plan_parser.add_argument("--split", type=int, default=None, help="Target number of workloads (e.g. 3, 5, 10).")
    plan_parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")

    args = parser.parse_args()

    if args.command == "tier":
        task_text = args.task
        if not task_text and not sys.stdin.isatty():
            task_text = sys.stdin.read().strip()
        if not task_text:
            task_text = "Standard software development task"

        result = classify_tier(task_text, args.files)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Recommended Tier: {result['tier'].upper()}")
            print(f"Rationale: {result['rationale']}")
            print(f"Relative Cost: {result['relative_cost']} ({result['token_budget_typical']})")
            print("Recommended Models:")
            for provider, model in result["model_recommendations"].items():
                print(f"  - {provider}: {model}")

    elif args.command == "plan":
        spec_text = args.spec
        if not spec_text and not sys.stdin.isatty():
            spec_text = sys.stdin.read().strip()
        if not spec_text:
            spec_text = "Scaffold full-stack application with .NET backend, React frontend, and Bicep infrastructure"

        plan = generate_plan(spec_text, args.split)
        if args.format == "json":
            print(json.dumps(plan, indent=2))
        else:
            print(f"# {plan['title']}\n")
            print("| Role | Work Package | Tier | Recommended Model | Verification Command |")
            print("|---|---|---|---|---|")
            for wp in plan["work_packages"]:
                print(f"| `{wp['role']}` | {wp['title']} | **{wp['tier'].title()}** | `{wp['model']}` | `{wp['verification_command']}` |")
            print("\n### Execution Rules")
            for r in plan["execution_rules"]:
                print(f"- {r}")


if __name__ == "__main__":
    main()
