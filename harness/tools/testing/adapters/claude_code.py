#!/usr/bin/env python3
"""Claude Code adapter for run_candidate.py (headless print mode).

Only project settings are loaded, so the user's global instructions, MCP servers and slash commands do not
reach the candidate; its context is the workspace (CLAUDE.md -> AGENTS.md). Tools are an explicit allowlist
rather than a permission bypass, so the agent can edit and run dotnet and git but little else. This narrows
access; it is not isolation. Disallow rules for --deny-path use Claude Code's path syntax and are unverified;
the runner's forbidden-reference scan of the trace is the check that counts.
"""
import sys

import common

# The last three mirror what install.sh and the repo's verify command give a real install: the harness's own
# scaffold command and the repo's verify command (T.1). Nothing else outside dotnet, git, ls and mkdir is allowed.
ALLOWED = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(dotnet *)", "Bash(git *)", "Bash(ls *)", "Bash(mkdir *)",
           "Bash(.harness/tools/greenfield/greenfield-init.sh *)", "Bash(.harness/tools/greenfield/greenfield-init.sh)",
           "Bash(scripts/verify.sh *)", "Bash(scripts/verify.sh)", "Bash(bash scripts/verify.sh *)", "Bash(bash scripts/verify.sh)"]


def main():
    args = common.parse_args(__doc__)
    command = [*common.resolve(args.executable, "claude"), "-p", "--model", args.model,
               "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits",
               "--setting-sources", "project", "--strict-mcp-config", "--disable-slash-commands",
               "--no-session-persistence", "--allowedTools", *ALLOWED]
    denied = [f"{tool}({common.drive_form(p)}/**)" for p in args.deny_path for tool in ("Read", "Edit", "Write")]
    if denied:
        command += ["--disallowedTools", *denied]
    code, events = common.stream(command, args, "claude")
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    tools = sum(1 for e in events if e.get("type") == "assistant"
                for block in e.get("message", {}).get("content", []) if block.get("type") == "tool_use")
    if result:
        usage = result.get("usage", {})
        common.write_usage(args, {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                                  "cost": result.get("total_cost_usd"), "retries": None, "tool_calls": tools,
                                  "turns": result.get("num_turns"), "model_reported": list(result.get("modelUsage", {}))})
    return code


if __name__ == "__main__":
    sys.exit(main())
