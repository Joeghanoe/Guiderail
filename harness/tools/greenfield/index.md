# Greenfield tools

Start a new repo or service design-first (rule DEL.4; playbook: [start-greenfield](../../playbooks/start-greenfield.md)).

Use `tvh greenfield init --target <dir> --profile service` or `--profile web-app`. Initialize Git for a standalone repo, then run `tvh verify --repo <dir> --design`. The [CLI contract](../cli/index.md) records execution separately from approval. The scripts below remain the internal implementation.

* `bash greenfield-init.sh [--service] [dir]` writes the skeletons a new repo owns: `docs/solution-design.md`,
  `AGENTS.md`, and the project verify in `~/.golden-path-harness/projects/<repo-id>/` (via `tools/code/project-verify.sh`, not into the repo). It copies this bundle's templates,
  carries no project shape of its own, and never overwrites a file. `--service` selects the stricter profile for a service that runs operations; `--web-app` the profile for an HTTP application.
* `design-check.py [dir] [--profile generic|service|web-app] [--json]` is the static gate (gate: [design-check](../../gates/design-check.md)).
  The project verify runs it first, in both modes. It reads files only and never runs the repo's code.
