#!/usr/bin/env python3
"""Deterministic check for the IaC settings rules that are a single obvious value: IAC.2, IAC.3, IAC.4.

Input:  changed paths on stdin (one per line, relative to the current directory); optionally the PR description.
Output: `path:line: RULE message` per hit; exit 1 on any hit unless the description has a waiver line
        `iac: n/a - <reason of at least 10 characters>`.

It only reports a setting that is explicitly set to the wrong value. A setting that is missing is not
reported (that is review). Bicep (.bicep) and HCL (.tf) files only.

Example:
  git diff --name-only origin/main...HEAD | python3 .harness/tools/iac/check-iac.py --description pr.txt
"""

import argparse
import pathlib
import re
import sys

WAIVER = re.compile(r"^\s*iac:\s*n/a\s*-\s*(.{10,})$", re.I | re.M)
SUFFIXES = {".bicep", ".tf"}


def setting(keys, values):
    """Key, `:` or `=`, then the wrong value, quoted or not (Bicep 'x', HCL "x"), ending the line or its object."""
    return re.compile(rf"\b(?:{keys})\b\s*[:=]\s*['\"]?(?:{values})['\"]?\s*[,}}]*\s*(?:$|//|#)", re.I)


CHECKS = [
    ("IAC.2", "network default action is Allow; use Deny with bypass AzureServices",
     setting("defaultAction|default_action", "Allow")),
    ("IAC.3", "minimum TLS version below 1.2",
     setting("minTlsVersion|minimumTlsVersion|min_tls_version|minimum_tls_version",
             r"1\.0|1\.1|TLS1_0|TLS1_1|Tls10|Tls11|TLS10|TLS11")),
    ("IAC.4", "Key Vault soft delete, purge protection or RBAC authorization switched off",
     setting("enableSoftDelete|enablePurgeProtection|enableRbacAuthorization|purge_protection_enabled|"
             "enable_rbac_authorization", "false")),
]


def scan(path):
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for rule, message, pattern in CHECKS:
            if pattern.search(line):
                yield f"{path}:{number}: {rule} {message}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--description", help="file with the PR description, for the waiver line")
    args = parser.parse_args()
    paths = [pathlib.Path(p.strip()) for p in sys.stdin if p.strip()]
    hits = [hit for p in paths if p.suffix in SUFFIXES and p.is_file() for hit in scan(p)]
    for hit in hits:
        print(hit)
    description = pathlib.Path(args.description).read_text(encoding="utf-8") if args.description else ""
    if hits and WAIVER.search(description):
        print("iac check: waived by the PR description")
        return 0
    print(f"iac check: {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
