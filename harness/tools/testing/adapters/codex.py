#!/usr/bin/env python3
"""Codex CLI adapter for run_candidate.py (non-interactive exec).

The workspace-write sandbox limits writes to the workspace; reads are not restricted, so this narrows access
and is not isolation. The user's config.toml is not loaded (auth still is) and the session is not persisted.
Codex reads AGENTS.md natively. Forbidden reads are detected by the runner's trace scan, not prevented.
"""
import sys

import common


def main():
    args = common.parse_args(__doc__)
    last = common.pathlib.Path(args.trace_dir) / "codex-last-message.txt"
    command = [*common.resolve(args.executable, "codex"), "exec", "--json", "-C", args.workspace, "-m", args.model,
               "-s", "workspace-write", "--ephemeral", "--ignore-user-config", "-o", str(last), "-"]
    code, events = common.stream(command, args, "codex")
    completed = [e for e in events if e.get("type") == "turn.completed"]
    if completed:
        usage = [e.get("usage", {}) for e in completed]
        total = lambda key: sum(u.get(key) or 0 for u in usage)
        tools = sum(1 for e in events if e.get("type") == "item.completed"
                    and e.get("item", {}).get("type") in {"command_execution", "file_change", "mcp_tool_call"})
        common.write_usage(args, {"input_tokens": total("input_tokens"), "output_tokens": total("output_tokens"),
                                  "cost": None, "retries": None, "tool_calls": tools, "turns": len(completed),
                                  "cost_reason": "Codex reports tokens, not cost"})
    return code


if __name__ == "__main__":
    sys.exit(main())
