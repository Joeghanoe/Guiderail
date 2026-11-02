#!/usr/bin/env python3
"""Antigravity CLI grader adapter for run_brownfield.py."""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Antigravity grader adapter")
    parser.add_argument("--prompt-file", help="path to prompt file")
    parser.add_argument("--model", default="gemini-3.8-flash-low", help="model to use")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.prompt_file:
        prompt = pathlib.Path(args.prompt_file).read_text(encoding="utf-8", errors="replace")
    else:
        prompt = sys.stdin.read()

    # Clean any embedded null bytes from binary diffs or inputs
    prompt = prompt.replace("\x00", "")

    executable = shutil.which("agy") or "agy"
    command = [
        executable,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--mode", "plan",
        "--model", args.model,
        "--dangerously-skip-permissions",
    ]
    stream_input = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"

    res = subprocess.run(command, input=stream_input, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr or f"agy failed with code {res.returncode}\n")
        return res.returncode

    response_text = ""
    for line in res.stdout.splitlines():
        try:
            event = json.loads(line)
            if event.get("event") == "result":
                response_text = event.get("result", {}).get("response", "")
        except ValueError:
            pass

    if not response_text:
        response_text = res.stdout

    print(response_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
