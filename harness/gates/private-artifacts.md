---
type: Gate
title: "Private artifact check"
description: The harness checkout contains no mined private review comments or raw evaluation outputs.
tool: harness/tools/harness/bundle.py privacy-check
owner: human:joeghanoe
status: stable
tags: [harness, privacy]
---

# Coverage

Scans `feedback/mined/` and the legacy `evals/results/` location for files and symlinks. CI runs the check
against the harness checkout.

# Blind spots

This is a path-specific guard, not a secrets scanner. It does not inspect Git history or files outside the
checkout.

# Failure behaviour

Exit 1 and list artifact paths without reading or printing their contents.

# Exception route

None: remove private artifacts from the checkout and keep generated evaluation output in the CI artifact or
system temporary directory.

# Refresh trigger

Change the list of private local-only artifact locations.
