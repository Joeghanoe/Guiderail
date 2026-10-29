"""Stand-in for the claude CLI: records its argv and prompt, emits stream-json like Claude Code's."""
import json
import pathlib
import sys

prompt = sys.stdin.read()
pathlib.Path("seen.json").write_text(json.dumps({"argv": sys.argv[1:], "prompt": prompt}), encoding="utf-8")
print(json.dumps({"type": "system", "subtype": "init"}))
print(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}, {"type": "text", "text": "x"}]}}))
print("not json")
print(json.dumps({"type": "result", "total_cost_usd": 0.5, "num_turns": 3, "usage": {"input_tokens": 100, "output_tokens": 20},
                  "modelUsage": {"claude-sonnet-5-5": {}}}))
