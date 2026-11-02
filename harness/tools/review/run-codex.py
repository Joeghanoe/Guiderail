#!/usr/bin/env python3
"""Invoke Codex CLI in a read-only sandbox and write its review response and usage.json."""

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time


MAX_TIMEOUT_SECONDS = 180
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", MAX_TIMEOUT_SECONDS))))
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "CODEX_HOME",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "OPENAI_API_KEY", "OPENAI_BASE_URL",
                   "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")


def load_usage():
    """usage.py beside this file; -I leaves the script folder off sys.path."""
    spec = importlib.util.spec_from_file_location("review_usage", pathlib.Path(__file__).with_name("usage.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


usage = load_usage()


def error_text(result):
    """The engine's own error message. With --json it arrives as events on stdout, not on stderr."""
    messages = []
    for text in result.stdout.splitlines():
        try:
            event = json.loads(text)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "error" and event.get("message"):
            messages.append(str(event["message"]))
        elif event.get("type") == "turn.failed":
            messages.append(str((event.get("error") or {}).get("message") or "turn failed"))
    return (result.stderr.strip() + "\n" + "\n".join(messages)).strip() or result.stdout.strip()


def main():
    if len(sys.argv) != 5:
        print("usage: run-codex.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, review_dir, _ = map(pathlib.Path, sys.argv[1:])
    command = [
        shutil.which("codex") or "codex", "exec",
        "--sandbox", "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--json",
        "--output-last-message", str(output_path),
        "-",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command[2:2] = ["--model", model]
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    started = time.monotonic()
    try:
        result = subprocess.run(command, input=prompt_path.read_text(encoding="utf-8"), capture_output=True,
                                text=True, timeout=TIMEOUT_SECONDS, check=False, env=environment)
    except FileNotFoundError:
        print("review: Codex CLI was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        usage.write(review_dir, "codex", model, time.monotonic() - started,
                    cost_reason="timed out before Codex reported usage")
        print(f"review: Codex CLI exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124
    usage.write(review_dir, "codex", model, time.monotonic() - started, **usage.from_codex(result.stdout))

    if result.returncode:
        message = error_text(result)
        if message:
            print(message[-2000:], file=sys.stderr)
        else:
            print(f"review: Codex CLI exited with status {result.returncode}", file=sys.stderr)
        return result.returncode
    if not output_path.is_file() or not output_path.read_text(encoding="utf-8").strip():
        print("review: Codex CLI returned an empty response", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
