---
type: Gate
title: "Secret scanning with Gitleaks (SEC.2)"
description: A pinned Gitleaks CLI scans the working tree or selected Git commit range and retains redacted findings.
tool: harness/tools/verification/verify.py gitleaks, versions and downloads in tools/verification/tool-lock.json
owner: team:teamvalue-aicoe
status: stable
tags: [security, verification]
---

# Execution

Harness CI scans the current tree, including new files. The reusable PR pipeline scans commits after the pinned PR merge base. A local command can scan the working tree, a range or all reachable HEAD history. Installation is a separate, checksum-verified step; verification never downloads tools.

# Policy source

Gitleaks owns detection rules. `tools/verification/gitleaks.toml` extends its pinned defaults. The shared `gitleaks.ignore` contains three exact historical fingerprints for deliberately synthetic redaction fixtures. It excludes no directory or file generally. Current fixtures construct those test strings at runtime. New commits and generated-secret calibration cases remain scanned. Repository-local ignore files and inline allow comments do not waive the shared check.

# Evidence and limits

The adapter retains rule IDs, locations and fingerprints; secret and match values are omitted. Scanner logs use full redaction. Errors are distinct from detected leaks. A positive scanner result establishes that its patterns found no leaks in the declared scope; it cannot prove absence of novel secrets, personal data, runtime leaks or prompt disclosure.

A finding requires remediation or a reviewed, narrow policy exception. Exposed real credentials require rotation; deleting a source line does not undo exposure. No blanket history baseline is installed.
