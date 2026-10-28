#!/usr/bin/env python3
"""Invoke the Antigravity CLI (agy) in plan mode and write its review response.

Each call is a new conversation (no --continue), so one review is one session. Plan mode does not edit the
workspace, but unlike the Claude and Copilot engines agy has no tool allowlist: its guarantee is weaker.
"""

import os
import pathlib
import subprocess
import sys


MAX_TIMEOUT_SECONDS = 180
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", MAX_TIMEOUT_SECONDS))))
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
                   "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")


# Headless agy auto-denies shell commands and then prints nothing, so say up front which tools to use.
TOOL_NOTICE = ("Use only your file read, search and list tools. Never run shell commands; they are denied "
               "and the review is lost.\n\n")


def main():
    if len(sys.argv) != 5:
        print("usage: run-agy.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, review_dir, bundle_dir = map(pathlib.Path, sys.argv[1:])
    command = [
        "agy", "--print", TOOL_NOTICE + prompt_path.read_text(encoding="utf-8"),
        "--mode", "plan", "--output-format", "text",
        "--add-dir", str(review_dir), "--add-dir", str(bundle_dir),
        "--print-timeout", f"{TIMEOUT_SECONDS}s",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command.extend(["--model", model])
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS + 15, check=False,
                                env=environment)
    except FileNotFoundError:
        print("review: agy was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"review: agy exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124

    if result.returncode:
        message = result.stderr or result.stdout
        print(message.strip()[-2000:] if message else f"review: agy exited with status {result.returncode}",
              file=sys.stderr)
        return result.returncode

    if not result.stdout.strip():
        print("review: agy returned an empty response" + (f": {result.stderr.strip()[-600:]}" if result.stderr.strip() else ""),
              file=sys.stderr)
        return 1
    output_path.write_text(result.stdout, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
