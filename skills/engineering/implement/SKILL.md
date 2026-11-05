---
name: implement
description: Implement or refactor a scoped feature or fix using established repository conventions and approved requirements. Use when changing code; do not start specification or architecture interviews for an already bounded change.
---

# Implement verified slices

Inputs are the intended behavior, affected repository and established baseline or explicit paths. Preserve approved criteria and decision references. Ask only for missing decisions that block the work; do not invent acceptance criteria. Keep the change focused on its requested outcome.

Read [implementation slices](IMPLEMENT-IN-SLICES.md) for the edit/test loop and handoff. For a new service use [start greenfield](../../../harness/playbooks/start-greenfield.md); when adding a file family use [repository conventions](../../../harness/playbooks/scaffold-from-conventions.md). Read [workload planning](../../../harness/playbooks/orchestrate-workload.md) only when the work actually needs decomposition and delegation is authorized.

```bash
tvh context select --brief --changed --baseline <baseline>
tvh scaffold brief --raw -- --repo <repository> --kind service
tvh code types --raw -- App.cs --symbols none
tvh verify --repo .
```

Select rules for each new kind of file. Do not read secrets or dotenv files; use example configuration. Test observable behavior through injected I/O, configuration and time boundaries. For user-visible changes, use [frontend verification](../../../harness/playbooks/verify-frontend.md).

Deliver the diff scope, criteria-to-evidence mapping, verification receipts and unresolved questions to independent review. Missing checks remain incomplete. Local implementation does not authorize publication, cloud changes or release.
