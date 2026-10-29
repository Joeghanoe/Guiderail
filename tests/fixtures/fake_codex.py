"""Stand-in for the codex CLI: records its argv and prompt, emits exec --json events."""
import json
import pathlib
import sys

prompt = sys.stdin.read()
pathlib.Path("seen.json").write_text(json.dumps({"argv": sys.argv[1:], "prompt": prompt}), encoding="utf-8")
print(json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 3}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 5, "output_tokens": 1}}))
