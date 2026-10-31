#!/usr/bin/env python3
"""Show which parts of the harness agents actually used in finished runs. Reads traces only; never reruns anything.

Question it answers: what from the harness reached a decision, and what only costs context? Three signals per run,
all taken from the agent's own events (Claude Code `claude-events.jsonl`, Codex `codex-events.jsonl`):
  opened   a bundle file the agent read, searched or named in a command
  cited    a rule ID the agent wrote in its replies
  mentioned an AGENTS.base.md section's commands and files that the agent ran or named
It also lists commands the adapter's allowlist denied, split by cause, because a denied command that the harness
itself tells agents to run is a gap in the framework, not in the candidate.

Unused is not useless: hooks, CI and reviewers read files the agent never opens. Treat a file nobody opened in many
runs as a candidate to re-evaluate (step 6 review), never as one to delete. Nothing here edits the harness.
"""
import argparse
import json
import pathlib
import re
import sys
from collections import Counter

TRACES = ("claude-events.jsonl", "codex-events.jsonl")
BUNDLE_SUFFIXES = {".md", ".sh", ".py", ".json", ".mjs"}
RULE_ID = re.compile(r"^rule_id:\s*(\S+)", re.M)
ID_IN_TEXT = re.compile(r"\b(?:[A-Z]{2,5}\.\d+[a-z]?|P\d{1,2})\b")
BACKTICKED = re.compile(r"`([^`\n]{3,80})`")
HARNESS_COMMAND = re.compile(r"\.harness/|golden-path-harness|bundle\.py|design-check|greenfield-init|check-example|verify\.sh|cloud-read")
SHELL_WRITE = re.compile(r"<<|\bcat\s*>|\bsed\s+-i|\btee\b|python3?\s+(-I\s+)?(-\s|/tmp/)")
CD_PREFIX = re.compile(r"^\s*cd\s+\S+\s*(?:;|&&)\s*")
COMPOUND = re.compile(r"^\s*cd\s|&&|;|\||\$\(|`")


def events(run):
    for name in TRACES:
        path = run / "trace" / name
        if path.is_file():
            return [json.loads(line) for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                    if line.strip().startswith("{")]
    return []


def agent_activity(run):
    """(tool-call texts, reply texts) from what the agent itself did, never from tool results or start-up events."""
    calls, replies = [], []
    for event in events(run):
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    calls.append((block.get("name"), block.get("input") or {}, block.get("id")))
                elif block.get("type") == "text":
                    replies.append(block.get("text", ""))
        elif event.get("type") == "item.completed":  # codex
            item = event.get("item", {})
            if item.get("type") == "command_execution":
                calls.append(("Bash", {"command": item.get("command", "")}, item.get("id")))
            elif item.get("type") == "agent_message":
                replies.append(item.get("text", ""))
    return calls, replies


def call_text(name, args):
    return " ".join(str(v) for v in args.values()) if name != "Bash" else str(args.get("command", ""))


def denied_calls(run):
    """Commands the adapter's allowlist refused, each with a cause: harness-documented, shell-write, compound or other."""
    calls, _ = agent_activity(run)
    by_id = {call_id: (name, args) for name, args, call_id in calls}
    found = []
    for event in events(run):
        if event.get("type") == "system" and event.get("subtype") == "permission_denied":
            name, args = by_id.get(event.get("tool_use_id"), (event.get("tool_name"), {}))
            text = call_text(name, args)
            bare = CD_PREFIX.sub("", text)  # `cd /work; cmd` is the same command with a prefix the allowlist cannot match
            if SHELL_WRITE.search(bare):
                cause = "shell-write"
            elif name == "Bash" and HARNESS_COMMAND.search(bare):
                cause = "harness-documented"
            elif bare != text or COMPOUND.search(bare):
                cause = "compound"
            else:
                cause = "other"
            found.append({"tool": name, "command": text[:200], "cause": cause, "cd_prefix": bare != text})
    return found


def stop_hook_blocks(run):
    return sum(1 for e in events(run) if e.get("type") == "user" and "Stop hook feedback" in json.dumps(e.get("message", {}))[:400])


def bundle_files(run, fallback):
    root = run / "workspace" / ".harness"
    root = root if root.is_dir() else fallback
    return root, sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in BUNDLE_SUFFIXES)


def rule_ids(files, root):
    ids = {}
    for path in files:
        if path.suffix == ".md" and "rules" in path.relative_to(root).parts:
            match = RULE_ID.search(path.read_text(encoding="utf-8", errors="replace")[:1500])
            if match:
                ids[match.group(1)] = path.relative_to(root).as_posix()
    return ids


def base_sections(base):
    sections, title, body = [], "(intro)", []
    for line in base.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            sections.append((title, "\n".join(body)))
            title, body = line[3:].strip(), []
        body.append(line)
    sections.append((title, "\n".join(body)))
    return [(t, b) for t, b in sections if b.strip()]


def analyse(runs, bundle, base):
    opened, cited, run_ids = Counter(), Counter(), []
    denied, hooks, mention_text = [], 0, []
    universe, ids = {}, {}
    for run in runs:
        root, files = bundle_files(run, bundle)
        rels = [p.relative_to(root).as_posix() for p in files]
        for rel, path in zip(rels, files):
            universe[rel] = path.stat().st_size
        ids.update(rule_ids(files, root))
        calls, replies = agent_activity(run)
        texts = [call_text(n, a) for n, a, _ in calls]
        mention_text += texts + replies
        for rel in rels:
            if any(rel in t for t in texts):
                opened[rel] += 1
        reply_ids = set(ID_IN_TEXT.findall(" ".join(replies)))
        for rid in reply_ids & set(ids):
            cited[ids[rid]] += 1
        denied += [dict(d, run=run.name) for d in denied_calls(run)]
        hooks += stop_hook_blocks(run)
        run_ids.append(run.name)
    sections = []
    blob = "\n".join(mention_text)
    for title, body in base_sections(base) if base.is_file() else []:
        tokens = {t.strip() for t in BACKTICKED.findall(re.sub(r"```.*?```", "", body, flags=re.S)) if re.search(r"[/.]", t) or ID_IN_TEXT.fullmatch(t)}
        tokens |= set(ID_IN_TEXT.findall(body))
        hit = sorted(t for t in tokens if t.split()[0].split("/")[-1] in blob)
        sections.append({"section": title, "bytes": len(body.encode()), "referenced": hit, "tokens": len(tokens)})
    return {"runs": run_ids, "run_count": len(run_ids), "stop_hook_blocks": hooks, "universe_files": len(universe),
            "universe_bytes": sum(universe.values()), "opened": opened, "cited": cited, "sizes": universe,
            "denied": denied, "base_sections": sections}


def render(a):
    n = max(a["run_count"], 1)
    out = [f"# Harness usage across {a['run_count']} run(s)", "",
           f"Bundle in the workspace: {a['universe_files']} files, {a['universe_bytes'] // 1024} KiB. "
           f"Stop-hook corrections sent to agents: {a['stop_hook_blocks']}.", ""]
    out += ["## Always-loaded instructions (AGENTS.base.md): cost vs. use", "",
            "| section | bytes | commands/files/IDs the agent referenced |", "|---|---|---|"]
    for s in a["base_sections"]:
        used = ", ".join(f"`{t}`" for t in s["referenced"][:6]) or "nothing"
        out.append(f"| {s['section']} | {s['bytes']} | {used} ({len(s['referenced'])}/{s['tokens']}) |")
    out += ["", "## Bundle files the agents opened", ""]
    if a["opened"]:
        out += ["| file | runs | bytes |", "|---|---|---|"]
        out += [f"| {rel} | {c}/{n} | {a['sizes'][rel]} |" for rel, c in a["opened"].most_common(25)]
    else:
        out.append("No bundle file was opened in any run: the always-loaded instructions and the hooks did all the work.")
    unopened = [r for r in a["sizes"] if r not in a["opened"]]
    out += ["", f"Never opened: {len(unopened)} of {a['universe_files']} files, "
            f"{sum(a['sizes'][r] for r in unopened) // 1024} KiB. By folder:", ""]
    folders = Counter(r.split("/")[0] for r in unopened)
    out += [f"- {f}: {c}" for f, c in folders.most_common()]
    out += ["", "## Rules the agents cited by ID in replies", ""]
    out += [f"- {rel}: {c}/{n}" for rel, c in a["cited"].most_common(20)] or ["- none"]
    out += ["", "## Commands the allowlist denied", ""]
    if not a["denied"]:
        out.append("- none")
    for cause, why in (("harness-documented", "commands the harness itself tells agents to run: propose an allowlist entry or fix the instruction"),
                       ("compound", "cd, pipes or && defeat a prefix allowlist: guide agents to single commands, or widen the pattern"),
                       ("shell-write", "agents write files through the shell instead of Edit/Write: model habit, not a framework gap"),
                       ("other", "unclassified: read them")):
        group = [d for d in a["denied"] if d["cause"] == cause]
        if group:
            counts = Counter(d["command"][:100] for d in group)
            out.append(f"- **{cause}** ({len(group)}): {why}")
            out += [f"  - {c}x `{' '.join(cmd.split())[:100]}`" for cmd, c in counts.most_common(5)]
            prefixed = sum(1 for d in group if d["cd_prefix"])
            if prefixed:
                out.append(f"  - {prefixed} of {len(group)} began with a `cd <dir>;` prefix")
    out += ["", "Unused is not useless: hooks, CI and reviewers read files agents never open. Re-evaluate, do not delete."]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True, help="finished run directories")
    parser.add_argument("--bundle", default=str(pathlib.Path(__file__).resolve().parents[2]),
                        help="bundle root, used when a run has no workspace/.harness")
    parser.add_argument("--base", default=str(pathlib.Path(__file__).resolve().parents[3] / "AGENTS.base.md"))
    parser.add_argument("--out", help="write the markdown report here as well")
    args = parser.parse_args()
    runs = [pathlib.Path(r).resolve(strict=True) for r in args.runs]
    text = render(analyse(runs, pathlib.Path(args.bundle), pathlib.Path(args.base)))
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
