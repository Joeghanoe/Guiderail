#!/usr/bin/env python3
"""Workload orchestration and model tiering tool for AI agent teams.

Decomposes complex milestones or multi-faceted tasks into decoupled subagent
work packages, recommends cost-effective model tiers (minimizing token usage
and cost), and validates completion gates.

Commands:
  tier     Evaluate task/diff complexity and recommend model tier and token budget
  plan     Decompose a task/spec into specialized subagent work packages (3-10 workloads)
  verify   Validate that subagent work packages pass their defined test gates

Vendor-neutral: the contract is the tier (economy, builder, reasoner). A model name is a lookup that rots and
differs per platform, so names live in models.json next to this file, layered under
~/.config/harness/models.json and --models FILE. No provider is the default: choose one with --provider or
HARNESS_MODEL_PROVIDER, or leave it out and take the tier to whatever model your own platform offers for it.
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import sys

# The tiers are the durable decision. Nothing here names a vendor or a model.
MODEL_TIERS = {
    "economy": {
        "description": "Fast, high-throughput, low-cost for rote tasks, linting, boilerplate, and regex verification",
        "relative_cost": "0.1x - 0.25x",
        "token_budget_typical": "2k - 10k tokens",
    },
    "builder": {
        "description": "Balanced, capable for standard feature development, components, endpoints, and test suites",
        "relative_cost": "1.0x",
        "token_budget_typical": "10k - 30k tokens",
    },
    "reasoner": {
        "description": "Deep reasoning, high-context for architecture design, security reviews, lead orchestration",
        "relative_cost": "3.0x - 5.0x",
        "token_budget_typical": "20k - 60k tokens",
    },
}

SHIPPED_MODELS = pathlib.Path(__file__).resolve().parent / "models.json"
CONFIG_HOME = pathlib.Path(os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config")
USER_MODELS = CONFIG_HOME / "harness" / "models.json"
PROVIDER_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")
STALE_AFTER_DAYS = 120   # a model name older than this is a lookup worth re-checking, not a fact


def fail(message: str) -> None:
    print(f"orchestrate.py: {message}", file=sys.stderr)
    sys.exit(1)


def clean_text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 120 or re.search(r"[\x00-\x1f\x7f]", value):
        fail(f"{what} must be a short single-line string")
    return value.strip()


def read_models(path: pathlib.Path) -> dict:
    """One config layer: {provider: {tier: name, reviewed: date}}. A bad file is an error, never silently skipped."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        fail(f"cannot read {path}: {error.strerror}")
    except ValueError:
        fail(f"{path} is not valid JSON")
    providers = data.get("providers") if isinstance(data, dict) else None
    if not isinstance(providers, dict):
        fail(f'{path} must look like {{"providers": {{"<name>": {{"economy": "...", "builder": "...", "reasoner": "..."}}}}}}')
    layer = {}
    for name, entry in providers.items():
        if not PROVIDER_NAME.match(name):
            fail(f"{path}: provider name {name!r} must be lowercase letters, digits, '.', '_' or '-'")
        if not isinstance(entry, dict):
            fail(f"{path}: provider {name} must be an object")
        unknown = sorted(set(entry) - set(MODEL_TIERS) - {"reviewed"})
        if unknown:
            fail(f"{path}: provider {name} has unknown key(s) {unknown}; tiers are {sorted(MODEL_TIERS)}")
        keys = [key for key in (*MODEL_TIERS, "reviewed") if key in entry]
        layer[name] = {key: clean_text(entry[key], f"{path}: {name}.{key}") for key in keys}
    return layer


def load_providers(extra: str | None = None) -> dict:
    """Shipped names, then the user's, then --models. A later layer replaces a provider entry wholesale, so a
    stale tier name cannot survive underneath a newer one."""
    providers = read_models(SHIPPED_MODELS)
    if USER_MODELS.is_file():
        providers.update(read_models(USER_MODELS))
    if extra:
        providers.update(read_models(pathlib.Path(extra)))
    return providers


def provider_age_days(entry: dict) -> int | None:
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(entry["reviewed"])).days
    except (KeyError, ValueError):
        return None


def describe_provider(name: str, entry: dict) -> dict:
    age = provider_age_days(entry)
    return {
        "provider": name,
        "models": {tier: entry[tier] for tier in MODEL_TIERS if tier in entry},
        "reviewed": entry.get("reviewed"),
        "stale": age is None or age > STALE_AFTER_DAYS,
    }


def resolve_provider(providers: dict, wanted: str | None) -> tuple[str | None, dict | None]:
    """The chosen provider's entry, or (None, None) when none was chosen. A name that is not configured is an
    error: a model name is never guessed."""
    name = wanted or os.environ.get("HARNESS_MODEL_PROVIDER") or None
    if name is None:
        return None, None
    if name not in providers:
        configured = ", ".join(sorted(providers)) or "none"
        fail(f"provider {name!r} is not configured (configured: {configured}). "
             f"Add it to {USER_MODELS} or pass --models FILE.")
    return name, providers[name]


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

    reasoner_matches = [m.group(0).strip() for m in (re.search(p, text_lower) for p in REASONER_KEYWORDS) if m]
    rote_matches = [m.group(0).strip() for m in (re.search(p, text_lower) for p in ROTE_KEYWORDS) if m]

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
            "deliverables": ["Code style and banned symbol checks", "Negative tests and boundary verification"],
            "verification_command": "scripts/verify.sh --fast || dotnet test",
            "file_boundary": ["tests/**", "Directory.Build.props"],
        })
        packages.append({
            "role": "domain-rules-engineer",
            "title": "Domain Entities & Pure Business Rules",
            "tier": "builder",
            "deliverables": ["Domain entities, value objects, and business rules", "Pure domain unit tests"],
            "verification_command": "dotnet test --filter Category=Domain",
            "file_boundary": ["src/**/*.Domain/**", "tests/**/*.Domain.Tests/**"],
        })
        packages.append({
            "role": "persistence-migration-engineer",
            "title": "Database Schema & EF Core Mapping",
            "tier": "builder",
            "deliverables": ["DbContext, entity configurations, soft-delete query filters", "Migration scripts"],
            "verification_command": "dotnet test --filter Category=Persistence",
            "file_boundary": ["src/**/*.Infrastructure/**", "src/**/Migrations/**"],
        })
        packages.append({
            "role": "api-controller-engineer",
            "title": "API Endpoints & Middleware",
            "tier": "builder",
            "deliverables": ["HTTP endpoints, correlation ID middleware, DTO validation", "Controller tests"],
            "verification_command": "dotnet test --filter Category=Api",
            "file_boundary": ["src/**/*.Api/**", "tests/**/*.Api.Tests/**"],
        })
        packages.append({
            "role": "integration-scenario-sentinel",
            "title": "Integration Scenarios & Health Probes",
            "tier": "builder",
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
            "deliverables": ["Automated guardrail test suite", "Linter and formatting alignment", "Illegal stack deprecation"],
            "verification_command": "scripts/verify.sh --fast || pnpm test",
            "file_boundary": ["tests/**", ".gitignore", "scripts/**"],
        })

        if any(k in text_lower for k in ["backend", ".net", "c#", "api", "database", "sql", "ef core", "endpoint"]):
            packages.append({
                "role": "dotnet-backend-builder",
                "title": "Backend Domain & API Implementation",
                "tier": "builder",
                "deliverables": ["Domain entities & authorization", "ASP.NET Core API", "xUnit unit & integration tests"],
                "verification_command": "dotnet test",
                "file_boundary": ["src/**/*.cs", "tests/**/*.cs", "*.sln"],
            })

        if any(k in text_lower for k in ["frontend", "react", "ui", "view", "vite", "typescript", "component", "tokens", "i18n"]):
            packages.append({
                "role": "react-frontend-builder",
                "title": "Frontend UI & Component Implementation",
                "tier": "builder",
                "deliverables": ["React views & components", "Brand token styles", "i18n localization", "Vitest component tests"],
                "verification_command": "pnpm test || npm test",
                "file_boundary": ["src/**/*.Web/**", "apps/web/**"],
            })

        if any(k in text_lower for k in ["infra", "bicep", "azure", "cloud", "deployment", "sql serverless", "swa"]):
            packages.append({
                "role": "bicep-infra-engineer",
                "title": "Infrastructure as Code & Cloud Modules",
                "tier": "builder",
                "deliverables": ["Bicep modules and parameter files", "Zero secrets compliance", "Infra validation tests"],
                "verification_command": "pnpm test tests/infra-rules.test.ts",
                "file_boundary": ["infra/**"],
            })

    # Always present: Lead Orchestrator & Reviewer
    packages.append({
        "role": "lead-orchestrator-reviewer",
        "title": "Lead Review, Integration & Verification Gate",
        "tier": "reasoner",
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

    # Shared by both commands: which provider's model names to resolve tiers to. Neither has a default.
    models = argparse.ArgumentParser(add_help=False)
    models.add_argument("--provider", default=None,
                        help="Resolve tiers to this provider's model names (else $HARNESS_MODEL_PROVIDER; "
                             "with neither, only the tier is given).")
    models.add_argument("--models", default=None, metavar="FILE",
                        help="Extra model names, same format as models.json; replaces a provider's entry wholesale.")

    tier_parser = subparsers.add_parser("tier", parents=[models],
                                        help="Classify task/diff complexity and recommend optimal model tier.")
    tier_parser.add_argument("--task", type=str, default="", help="Task or story description.")
    tier_parser.add_argument("--files", nargs="*", default=[], help="List of affected files.")
    tier_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format.")

    plan_parser = subparsers.add_parser("plan", parents=[models],
                                        help="Generate a multi-agent work package decomposition.")
    plan_parser.add_argument("--spec", type=str, default="", help="High level specification or backlog item.")
    plan_parser.add_argument("--split", type=int, default=None, help="Target number of workloads (e.g. 3, 5, 10).")
    plan_parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")

    args = parser.parse_args()
    providers = load_providers(args.models)
    chosen, entry = resolve_provider(providers, args.provider)
    stale_note = None
    if chosen:
        described = describe_provider(chosen, entry)
        if described["stale"]:
            when = described["reviewed"] or "no date recorded"
            stale_note = f"names for {chosen} were last checked: {when}; re-check them before relying on them."
    unchosen_note = (f"No provider chosen: take the tier to your platform's model for it, or pass --provider "
                     f"(configured: {', '.join(sorted(providers)) or 'none'}).")

    if args.command == "tier":
        task_text = args.task
        if not task_text and not sys.stdin.isatty():
            task_text = sys.stdin.read().strip()
        if not task_text:
            task_text = "Standard software development task"

        result = classify_tier(task_text, args.files)
        shown = [chosen] if chosen else sorted(providers)
        result["models"] = [
            {"provider": name, "model": providers[name].get(result["tier"]),
             "reviewed": providers[name].get("reviewed"), "stale": describe_provider(name, providers[name])["stale"]}
            for name in shown
        ]
        if not chosen:
            result["models_note"] = unchosen_note
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Recommended Tier: {result['tier'].upper()}")
            print(f"Rationale: {result['rationale']}")
            print(f"Relative Cost: {result['relative_cost']} ({result['token_budget_typical']})")
            for row in result["models"]:
                print(f"Model ({row['provider']}): {row['model'] or 'none recorded for this tier'}")
            print(stale_note if stale_note else ("" if chosen else unchosen_note))

    elif args.command == "plan":
        spec_text = args.spec
        if not spec_text and not sys.stdin.isatty():
            spec_text = sys.stdin.read().strip()
        if not spec_text:
            spec_text = "Scaffold full-stack application with .NET backend, React frontend, and Bicep infrastructure"

        plan = generate_plan(spec_text, args.split)
        plan["provider"] = chosen
        if chosen:
            for wp in plan["work_packages"]:
                wp["model"] = entry.get(wp["tier"])
        else:
            plan["models_note"] = unchosen_note
        if stale_note:
            plan["models_note"] = stale_note
        if args.format == "json":
            print(json.dumps(plan, indent=2))
        else:
            print(f"# {plan['title']}\n")
            if chosen:
                print("| Role | Work Package | Tier | Model | Verification Command |")
                print("|---|---|---|---|---|")
            else:
                print("| Role | Work Package | Tier | Verification Command |")
                print("|---|---|---|---|")
            for wp in plan["work_packages"]:
                head = f"| `{wp['role']}` | {wp['title']} | **{wp['tier'].title()}** |"
                model = f" `{wp['model']}` |" if chosen and wp.get("model") else (" - |" if chosen else "")
                print(f"{head}{model} `{wp['verification_command']}` |")
            if plan.get("models_note"):
                print(f"\n{plan['models_note']}")
            print("\n### Execution Rules")
            for r in plan["execution_rules"]:
                print(f"- {r}")


if __name__ == "__main__":
    main()
