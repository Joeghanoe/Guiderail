#!/usr/bin/env python3
"""Presence check for rule T.5: a changed component needs a changed scenario, or an explicit n/a.

Input:  changed paths on stdin (one per line); the repo's .harness-scenarios.json; optionally the PR description.
Output: one line per component; exit 1 when a component changed without a scenario and without an n/a line.

.harness-scenarios.json:
  [
    { "component": "tls.esb.b2b.case.external/**",
      "scenarios": ["tests/IntegrationPlatform.E2E/**/Features/B2B/**"] }
  ]

The PR description may waive the check per change with a line `e2e: n/a - <reason of at least 10 characters>`.

Example:
  git diff --name-only origin/main...HEAD | \\
    python3 .harness/tools/testing/check-scenarios.py --config .harness-scenarios.json --description pr.txt
"""

import argparse
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # keep the bundle free of __pycache__ folders
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "harness"))
from bundle import glob_to_regex  # noqa: E402

WAIVER = re.compile(r"^\s*e2e:\s*n/a\s*-\s*(.{10,})$", re.I | re.M)


def matches(patterns, paths):
    regexes = [glob_to_regex(p) for p in patterns]
    return [p for p in paths if any(r.match(p) for r in regexes)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=".harness-scenarios.json")
    parser.add_argument("--description", help="file with the PR description")
    args = parser.parse_args()

    config_path = pathlib.Path(args.config)
    if not config_path.is_file():
        print(f"check-scenarios: no {config_path}; this repo declares no integration suite, nothing to check")
        return 0
    components = json.loads(config_path.read_text(encoding="utf-8"))
    changed = [line.strip() for line in sys.stdin if line.strip()]
    description = pathlib.Path(args.description).read_text(encoding="utf-8") if args.description else ""
    waiver = WAIVER.search(description)

    missing = 0
    for c in components:
        touched = matches([c["component"]], changed)
        if not touched:
            continue
        scenarios = matches(c["scenarios"], changed)
        if scenarios:
            print(f"ok      {c['component']}: {len(touched)} file(s) changed, scenario(s): {', '.join(sorted(scenarios))}")
        elif waiver:
            print(f"waived  {c['component']}: e2e: n/a - {waiver.group(1).strip()}")
        else:
            missing += 1
            print(f"MISSING {c['component']}: {len(touched)} file(s) changed, no scenario under {', '.join(c['scenarios'])}")
    if missing:
        print("T.5: add or update a scenario for the changed behaviour, or add `e2e: n/a - <reason>` to the PR description.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
