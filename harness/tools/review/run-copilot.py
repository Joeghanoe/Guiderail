#!/usr/bin/env python3
"""Invoke GitHub Copilot CLI with read-only tools and write its review response."""

import os
import pathlib
import shutil
import subprocess
import sys


MAX_TIMEOUT_SECONDS = 180
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", MAX_TIMEOUT_SECONDS))))
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "COPILOT_HOME", "HTTPS_PROXY",
                   "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")


def main():
    if len(sys.argv) != 5:
        print("usage: run-copilot.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, review_dir, bundle_dir = map(pathlib.Path, sys.argv[1:])
    command = [
        shutil.which("copilot") or "copilot", "--prompt", prompt_path.read_text(encoding="utf-8"),
        "--silent", "--output-format=text",
        "--available-tools=read,grep,glob",
        "--allow-tool=read", "--allow-tool=grep", "--allow-tool=glob",
        "--disable-builtin-mcps",
        "--add-dir", str(review_dir),
        "--add-dir", str(bundle_dir),
        "--no-auto-update",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command.extend(["--model", model])
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False,
                                env=environment)
    except FileNotFoundError:
        print("review: Copilot CLI was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"review: Copilot CLI exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124

    if result.returncode:
        message = result.stderr or result.stdout
        if message:
            print(message.strip()[-2000:], file=sys.stderr)
        else:
            print(f"review: Copilot CLI exited with status {result.returncode}", file=sys.stderr)
        return result.returncode

    if not result.stdout.strip():
        print("review: Copilot CLI returned an empty response", file=sys.stderr)
        return 1
    output_path.write_text(result.stdout, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
