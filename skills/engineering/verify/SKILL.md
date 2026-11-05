---
name: verify
description: Verify a code change, user interface, or deployed version and report evidence before completion. Use for readiness and health checks; verification does not replace independent review or authorize deployment.
---

# Verify the intended scope

Inputs are the affected source revision or deployed version, approved criteria and required checks. Missing tools, failed checks, stale artifacts and timeouts remain explicit incomplete or failed evidence. Run mandatory checks even when native skill discovery did not select them.

Load only the route needed:

- Code change: run the project gate and any additional checks required by the repository.
- User-visible change: [frontend verification](../../../harness/playbooks/verify-frontend.md). Inspect screenshots and usability alongside automated checks.
- Deployed version: [deployment verification](../../../harness/playbooks/verify-deployment.md). Observe the intended environment, version and relevant time window through restricted readers.

```bash
tvh verify --repo .
tvh frontend contrast --raw -- --css <file> --pair <foreground>/<background>
tvh frontend capture --url <localhost-url>
tvh frontend compare --before <before-report-directory> --after <after-report-directory>
```

Comparison takes capture reports, not individual PNG files. Capture success alone proves neither accessibility nor usability. Do not skip required checks for prototype code.

Output source/version scope, commands, receipts, failures, skipped checks with reasons and residual judgment. Pass these artifacts to review or acceptance. Existing verification failures must reach the reviewer and block a clean result; a human authorizes promotion or release.
