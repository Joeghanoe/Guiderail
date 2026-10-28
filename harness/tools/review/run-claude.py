#!/usr/bin/env python3
"""Invoke Claude with bounded turns and wall-clock time, then write its review response."""

import json
import os
import pathlib
import subprocess
import sys


MAX_TURNS = 10
# Hard ceiling. HARNESS_REVIEW_TIMEOUT_SECONDS can only lower it, never raise it.
MAX_TIMEOUT_SECONDS = 180
TIMEOUT_SECONDS = min(MAX_TIMEOUT_SECONDS,
                      max(1, int(os.environ.get("HARNESS_REVIEW_TIMEOUT_SECONDS", MAX_TIMEOUT_SECONDS))))
# Only what the claude CLI needs to start and reach its provider; pipeline tokens and cloud credentials stay out.
# Keep identical to CLI_ENVIRONMENT in eval.py (tests/test_eval.py checks it).
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "CLAUDE_CONFIG_DIR",
                   "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
                   "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "AWS_REGION", "AWS_DEFAULT_REGION",
                   "AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_VERTEX_PROJECT_ID", "CLOUD_ML_REGION",
                   "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")


def main():
    if len(sys.argv) != 5:
        print("usage: run-claude.py <prompt> <output> <review-dir> <bundle-dir>", file=sys.stderr)
        return 2

    prompt_path, output_path, review_dir, bundle_dir = map(pathlib.Path, sys.argv[1:])
    command = [
        "claude", "-p", prompt_path.read_text(encoding="utf-8"),
        "--allowedTools", "Read,Grep,Glob",
        "--max-turns", str(MAX_TURNS),
        "--add-dir", str(review_dir),
        "--add-dir", str(bundle_dir),
        "--output-format", "json",
    ]
    model = os.environ.get("HARNESS_REVIEW_MODEL")
    if model:
        command.extend(["--model", model])
    environment = {key: os.environ[key] for key in CLI_ENVIRONMENT if key in os.environ}

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False,
                                env=environment)
    except subprocess.TimeoutExpired:
        print(f"review: claude exceeded the {TIMEOUT_SECONDS}s time limit", file=sys.stderr)
        return 124

    if result.returncode:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        else:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                payload = {}
            message = payload.get("result") if payload.get("is_error") else None
            if isinstance(message, str) and message:
                print(f"review: claude failed: {message}", file=sys.stderr)
            else:
                print(f"review: claude exited with status {result.returncode}", file=sys.stderr)
        return result.returncode

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        print(f"review: claude returned invalid JSON: {error}", file=sys.stderr)
        return 1
    response = payload.get("result")
    if not isinstance(response, str) or not response:
        print("review: claude response has no result text", file=sys.stderr)
        return 1
    output_path.write_text(response, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
