#!/usr/bin/env python3
"""Invoke GitHub Copilot CLI with read-only tools and write its review response and usage.json."""

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
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "COPILOT_HOME", "HTTPS_PROXY",
                   "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")
USAGE_FILE = "copilot-usage.json"


def load_usage():
    """usage.py beside this file; -I leaves the script folder off sys.path."""
    spec = importlib.util.spec_from_file_location("review_usage", pathlib.Path(__file__).with_name("usage.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


usage = load_usage()


def reported(review_dir):
    """What Copilot wrote to --usage-output-file, as usage fields."""
    try:
        document = json.loads((review_dir / USAGE_FILE).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"cost_reason": "the Copilot CLI wrote no usage file"}
    except ValueError:
        return {"cost_reason": "the Copilot usage file is not valid JSON"}
    return usage.from_usage_file(document)


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
        "--usage-output-file", str(review_dir / USAGE_FILE),
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command.extend(["--model", model])
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False,
                                env=environment)
    except FileNotFoundError:
        print("review: Copilot CLI was not found on PATH", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        usage.write(review_dir, "copilot", model, time.monotonic() - started,
                    cost_reason="timed out before Copilot reported usage")
        print(f"review: Copilot CLI exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124
    usage.write(review_dir, "copilot", model, time.monotonic() - started, **reported(review_dir))

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
