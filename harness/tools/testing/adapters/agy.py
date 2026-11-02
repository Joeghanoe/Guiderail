#!/usr/bin/env python3
"""Antigravity CLI adapter for run_candidate.py (headless exec mode)."""
import json
import pathlib
import signal
import sys

import common


def extract_usage(events, args, res=None):
    tools = sum(1 for e in events if e.get("event") == "step_update"
                and e.get("step_update", {}).get("step_type") == "tool"
                and e.get("step_update", {}).get("state") == "DONE")
    if res and res.get("usage"):
        u = res.get("usage", {})
        inp = u.get("input_tokens")
        out = u.get("output_tokens")
        cache = u.get("cache_read_tokens")
        turns = res.get("num_turns", 1)
    else:
        # Sum from step_updates
        inp = sum(e.get("step_update", {}).get("usage", {}).get("input_tokens", 0)
                  for e in events if e.get("step_update", {}).get("usage"))
        out = sum(e.get("step_update", {}).get("usage", {}).get("output_tokens", 0)
                  for e in events if e.get("step_update", {}).get("usage"))
        cache = sum(e.get("step_update", {}).get("usage", {}).get("cache_read_tokens", 0)
                    for e in events if e.get("step_update", {}).get("usage"))
        turns = sum(1 for e in events if e.get("event") == "step_update"
                    and e.get("step_update", {}).get("step_type") == "agent_response"
                    and e.get("step_update", {}).get("state") == "DONE") or 1
    return {
        "input_tokens": inp or None,
        "cached_input_tokens": cache or None,
        "output_tokens": out or None,
        "cost": None,
        "retries": None,
        "tool_calls": tools,
        "turns": turns,
        "model_reported": [args.model],
        "cost_reason": "Antigravity reports tokens, not cost",
    }


def main():
    args = common.parse_args(__doc__)
    prompt_text = pathlib.Path(args.prompt_file).read_text(encoding="utf-8")
    command = [
        *common.resolve(args.executable, "agy"),
        f"--print={prompt_text}",
        "--model", args.model,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]
    events = []

    def handle_sigterm(signum, frame):
        # Best effort write usage on timeout
        try:
            u = extract_usage(events, args)
            common.write_usage(args, u)
        except Exception:
            pass
        sys.exit(signum)

    signal.signal(signal.SIGTERM, handle_sigterm)

    code, events = common.stream(command, args, "agy")
    res = next((e.get("result", {}) for e in reversed(events) if e.get("event") == "result"), None)
    common.write_usage(args, extract_usage(events, args, res))
    return code


if __name__ == "__main__":
    sys.exit(main())
