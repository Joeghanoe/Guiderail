#!/usr/bin/env python3
"""Invoke Codex CLI in a read-only sandbox and write its review response."""

import os
import pathlib
import shutil
import subprocess
import sys


MAX_TIMEOUT_SECONDS = 180
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", MAX_TIMEOUT_SECONDS))))
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "CODEX_HOME",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "OPENAI_API_KEY", "OPENAI_BASE_URL",
                   "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")


def main():
    if len(sys.argv) != 5:
        print("usage: run-codex.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, _, _ = map(pathlib.Path, sys.argv[1:])
    command = [
        shutil.which("codex") or "codex", "exec",
        "--sandbox", "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--output-last-message", str(output_path),
        "-",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command[2:2] = ["--model", model]
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    try:
        result = subprocess.run(command, input=prompt_path.read_text(encoding="utf-8"), capture_output=True,
                                text=True, timeout=TIMEOUT_SECONDS, check=False, env=environment)
    except FileNotFoundError:
        print("review: Codex CLI was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"review: Codex CLI exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124

    if result.returncode:
        message = result.stderr or result.stdout
        if message:
            print(message.strip()[-2000:], file=sys.stderr)
        else:
            print(f"review: Codex CLI exited with status {result.returncode}", file=sys.stderr)
        return result.returncode
    if not output_path.is_file() or not output_path.read_text(encoding="utf-8").strip():
        print("review: Codex CLI returned an empty response", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
