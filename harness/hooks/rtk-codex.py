#!/usr/bin/env python3
"""Adapt RTK's Claude hook output to Codex's explicit rewrite permission contract."""
import json
import subprocess
import sys


def adapt(output):
    if not output.strip():
        return output
    data = json.loads(output)
    hook = data.get("hookSpecificOutput", {})
    # Older RTK releases omit this field. Never overwrite an explicit denial.
    if "updatedInput" in hook and "permissionDecision" not in hook:
        hook["permissionDecision"] = "allow"
    return json.dumps(data) + "\n"


def main():
    result = subprocess.run(
        ["rtk", "hook", "claude"], input=sys.stdin.read(), capture_output=True, text=True
    )
    sys.stderr.write(result.stderr)
    sys.stdout.write(adapt(result.stdout) if result.returncode == 0 else result.stdout)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
