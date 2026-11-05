#!/usr/bin/env python3
"""Invoke the Antigravity CLI (agy) in plan mode and write its review response.

Each call is a new conversation (no --continue), so one review is one session. Plan mode does not edit the
workspace, but unlike the Claude and Copilot engines agy has no tool allowlist: its guarantee is weaker.
"""

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time


DEFAULT_TIMEOUT_SECONDS = 240
MAX_TIMEOUT_SECONDS = max(DEFAULT_TIMEOUT_SECONDS, int(os.environ.get("HARNESS_REVIEW_MAX_TIMEOUT_SECONDS", "300")))
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))))
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
                   "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS",
                   "HARNESS_REVIEW_TIMEOUT_SECONDS", "HARNESS_REVIEW_MAX_TIMEOUT_SECONDS")


# Headless agy auto-denies shell commands and then prints nothing, so say up front which tools to use.
TOOL_NOTICE = ("Use only your file read, search and list tools. Never run shell commands; they are denied "
               "and the review is lost.\n"
               "Complete your review within 5 tool turns: read only selected.json, changed.txt, diff.patch, "
               "and the selected rule and example files. Do not explore test harness, git or eval internals. "
               "Output only the JSON array.\n\n")
NO_USAGE = "agy reports no usage; only the time is measured"


def load_usage():
    """usage.py beside this file; -I leaves the script folder off sys.path."""
    spec = importlib.util.spec_from_file_location("review_usage", pathlib.Path(__file__).with_name("usage.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


usage = load_usage()


def main():
    if len(sys.argv) != 5:
        print("usage: run-agy.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, review_dir, bundle_dir = map(pathlib.Path, sys.argv[1:])
    command = [
        shutil.which("agy") or "agy", "--print", TOOL_NOTICE + prompt_path.read_text(encoding="utf-8"),
        "--mode", "plan", "--output-format", "json",
        "--dangerously-skip-permissions",
        "--add-dir", str(review_dir), "--add-dir", str(bundle_dir),
        "--add-dir", str(bundle_dir.resolve().parent / "skills"),
        "--print-timeout", f"{TIMEOUT_SECONDS}s",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command.extend(["--model", model])
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS + 15, check=False,
                                env=environment)
    except FileNotFoundError:
        print("review: agy was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        usage.write(review_dir, "agy", model, time.monotonic() - started,
                    cost_reason="timed out before agy reported usage")
        print(f"review: agy exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124

    wall_seconds = time.monotonic() - started
    payload = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except ValueError:
            pass

    usage_data = usage.from_agy(payload) if payload else {"cost_reason": NO_USAGE}
    usage.write(review_dir, "agy", model, wall_seconds, **usage_data)

    if result.returncode:
        message = result.stderr or result.stdout
        print(message.strip()[-2000:] if message else f"review: agy exited with status {result.returncode}",
              file=sys.stderr)
        return result.returncode

    response_text = payload.get("response", "") if isinstance(payload, dict) else result.stdout
    if not response_text.strip():
        print("review: agy returned an empty response" + (f": {result.stderr.strip()[-600:]}" if result.stderr.strip() else ""),
              file=sys.stderr)
        return 1
    output_path.write_text(response_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
