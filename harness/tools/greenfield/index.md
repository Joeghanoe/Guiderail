# Greenfield tools

Start a new repo or service design-first (rule DEL.4; playbook: [start-greenfield](../../playbooks/start-greenfield.md)).

* `bash greenfield-init.sh [--service] [dir]` writes the skeletons a new repo owns: `docs/solution-design.md`,
  `AGENTS.md`, `scripts/verify.sh`. It copies this bundle's templates,
  carries no project shape of its own, and never overwrites a file. `--service` selects the stricter profile for a service that runs operations; `--web-app` the profile for an HTTP application.
* `design-check.py [dir] [--profile generic|service|web-app] [--json]` is the static gate (gate: [design-check](../../gates/design-check.md)).
  `scripts/verify.sh` runs it first, in both modes. It reads files only and never runs the repo's code.
