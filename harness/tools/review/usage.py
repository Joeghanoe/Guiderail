#!/usr/bin/env python3
"""Tokens, cost and time per review run (ADR 0007 decision 3).

Each review adapter (run-*.py) writes `<review-dir>/usage.json` with `write()`. eval.py and eval-queue.py add runs
up with `total()`, and the PR pipeline copies the file into its receipt.

What the engine does not report stays null, never 0 (ADR 0006 item 7), and `cost_reason` says where a cost came
from or why there is none. The field names match the benchmark adapters (tools/testing/adapters):
  input_tokens         all input, cached included
  cached_input_tokens  the part of input_tokens served from the provider's cache
  output_tokens        output, reasoning included where the engine counts it
  cost                 USD: as the engine reports it, else estimated from your price file, else null
  wall_seconds         the adapter's own clock around the engine call

Price file (optional, yours, never committed): ~/.config/harness/prices.json, or $HARNESS_PRICES.
  {"checked": "2026-10-31",
   "models": {"<model as passed with --model>": {"input_per_mtok": 1.25, "cached_input_per_mtok": 0.125,
                                                 "output_per_mtok": 10.0}}}
A price older than STALE_DAYS is still used, and the cost_reason says it is stale.
"""

import datetime
import json
import os
import pathlib

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "cost", "wall_seconds")
FILE = "usage.json"
STALE_DAYS = 120


def prices_path():
    configured = os.environ.get("HARNESS_PRICES")
    return pathlib.Path(configured) if configured else pathlib.Path.home() / ".config" / "harness" / "prices.json"


def price(model, input_tokens, cached_input_tokens, output_tokens, path=None, today=None):
    """(cost, reason) from the price file, or (None, why not)."""
    if input_tokens is None or output_tokens is None:
        return None, "no token counts to price"
    if not model or model == "default":
        return None, "model not pinned; pass --model to price it"
    path = path or prices_path()
    try:
        table = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"no price file ({path})"
    except ValueError:
        return None, f"price file is not valid JSON ({path})"
    rates = table.get("models", {}).get(model)
    if not rates:
        return None, f"model {model} is not in {path}"
    cached = cached_input_tokens or 0
    per_input = rates["input_per_mtok"]
    per_cached = rates.get("cached_input_per_mtok", per_input)
    cost = ((input_tokens - cached) * per_input + cached * per_cached + output_tokens * rates["output_per_mtok"]) / 1e6
    checked = table.get("checked", "unknown date")
    reason = f"estimated from {path.name}, prices checked {checked}"
    try:
        age = ((today or datetime.date.today()) - datetime.date.fromisoformat(checked)).days
        if age > STALE_DAYS:
            reason += f" (stale: {age} days old)"
    except ValueError:
        reason += " (unknown age)"
    return round(cost, 6), reason


def record(engine, model, wall_seconds, input_tokens=None, cached_input_tokens=None, output_tokens=None,
           cost=None, cost_reason=None, **extra):
    """One run's usage. A cost the engine did not report is estimated from the price file when it can be."""
    if cost is None:
        cost, priced = price(model, input_tokens, cached_input_tokens, output_tokens)
        cost_reason = priced if cost is not None or not cost_reason else f"{cost_reason}; {priced}"
    entry = {"engine": engine, "model": model or "default", "input_tokens": input_tokens,
             "cached_input_tokens": cached_input_tokens, "output_tokens": output_tokens, "cost": cost,
             "cost_reason": cost_reason, "wall_seconds": round(wall_seconds, 1) if wall_seconds is not None else None}
    entry.update(extra)
    return entry


def write(review_dir, *args, **kwargs):
    entry = record(*args, **kwargs)
    (pathlib.Path(review_dir) / FILE).write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return entry


def read(review_dir):
    try:
        return json.loads((pathlib.Path(review_dir) / FILE).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def total(items):
    """Sum of runs or of earlier totals. A field nobody reported stays null; the counts say how many runs did."""
    out = {"runs": 0, "runs_with_tokens": 0, "runs_with_cost": 0}
    sums = dict.fromkeys(FIELDS)
    for item in items:
        item = item or {}   # a run without usage.json counts as a run with nothing known
        runs = item.get("runs", 1)
        out["runs"] += runs
        out["runs_with_tokens"] += item.get("runs_with_tokens", runs if item.get("input_tokens") is not None else 0)
        out["runs_with_cost"] += item.get("runs_with_cost", runs if item.get("cost") is not None else 0)
        for field in FIELDS:
            if item.get(field) is not None:
                sums[field] = (sums[field] or 0) + item[field]
    out.update({field: round(value, 6) if isinstance(value, float) else value for field, value in sums.items()})
    return out


def describe(summary):
    """One readable line for a total."""
    if not summary or not summary.get("runs"):
        return "no runs"
    tokens = (f"{summary['input_tokens']:,} in ({summary['cached_input_tokens'] or 0:,} cached), "
              f"{summary['output_tokens'] or 0:,} out" if summary.get("input_tokens") is not None else "tokens unknown")
    cost = f"${summary['cost']:.4f}" if summary.get("cost") is not None else "cost unknown"
    wall = f"{summary['wall_seconds']:.0f}s" if summary.get("wall_seconds") is not None else "time unknown"
    return (f"{summary['runs']} runs: {tokens}; {cost}; {wall} "
            f"(tokens for {summary['runs_with_tokens']}, cost for {summary['runs_with_cost']})")


# What each engine reports.

def from_claude(payload):
    """Claude CLI --output-format json. Its input_tokens excludes cache; ours includes it."""
    usage = payload.get("usage") or {}
    parts = [usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
    known = [p for p in parts if p is not None]
    cost = payload.get("total_cost_usd")
    return {"input_tokens": sum(known) if known else None, "cached_input_tokens": usage.get("cache_read_input_tokens"),
            "output_tokens": usage.get("output_tokens"), "cost": cost,
            "cost_reason": "reported by the Claude CLI (API list price; a subscription bills differently)"
            if cost is not None else "the Claude CLI reported no cost"}


def from_codex(stdout):
    """Codex exec --json events: one turn.completed with usage per turn. OpenAI input already includes cached."""
    usages = []
    for text in stdout.splitlines():
        try:
            event = json.loads(text)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usages.append(event["usage"])
    if not usages:
        return {"cost_reason": "Codex reported no usage"}
    add = lambda key: sum(u.get(key) or 0 for u in usages)
    return {"input_tokens": add("input_tokens"), "cached_input_tokens": add("cached_input_tokens"),
            "output_tokens": add("output_tokens") + add("reasoning_output_tokens"),
            "cost_reason": "Codex reports tokens, not cost"}


KEYS = {
    "input_tokens": {"inputtokens", "prompttokens"},
    "cached_input_tokens": {"cachedinputtokens", "cachereadtokens", "cachereadinputtokens"},
    "output_tokens": {"outputtokens", "completiontokens"},
    "cost": {"totalcostusd", "costusd"},
    "premium_requests": {"premiumrequests", "totalpremiumrequests"},
}


def _norm(key):
    return str(key).replace("_", "").replace("-", "").lower()


def _usage_dicts(value):
    """The highest dicts that carry token counts; a 'total' entry wins over its siblings, so nothing counts twice."""
    if isinstance(value, list):
        return [d for item in value for d in _usage_dicts(item)]
    if not isinstance(value, dict):
        return []
    if any(_norm(k) in KEYS["input_tokens"] | KEYS["output_tokens"] for k in value):
        return [value]
    for key, child in value.items():
        if _norm(key) in ("total", "totals", "summary") and _usage_dicts(child):
            return _usage_dicts(child)
    return [d for child in value.values() for d in _usage_dicts(child)]


def from_usage_file(document):
    """A usage file whose exact shape we do not pin (Copilot's --usage-output-file). Unknown shape: all null."""
    found = {}
    dicts = _usage_dicts(document)
    for field, names in KEYS.items():
        values = [v for d in dicts for k, v in d.items() if _norm(k) in names and isinstance(v, (int, float))]
        if not values and isinstance(document, dict):   # premium requests and cost may sit beside the token dicts
            values = [v for k, v in document.items() if _norm(k) in names and isinstance(v, (int, float))]
        found[field] = sum(values) if values else None
    reason = "reported by the Copilot CLI" if found["cost"] is not None else "the Copilot CLI reported no cost"
    if found["input_tokens"] is None and found["output_tokens"] is None:
        reason = "the Copilot usage file had no token counts this parser recognises"
    return {**found, "cost_reason": reason}
