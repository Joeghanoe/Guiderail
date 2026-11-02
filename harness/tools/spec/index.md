# Spec Tools

Places a spec note in the user's Obsidian vault and keeps its front matter. The spec itself is written by the
agent and the user together; this tool only decides *where* the note goes and refuses to write anywhere else.
Playbook: [write-spec.md](../../playbooks/write-spec.md).

## Routing table

| When the user says | Tool / Playbook | Command |
|---|---|---|
| "write a spec" / "what does done mean here?" | Spec playbook | `~/.golden-path-harness/harness/playbooks/write-spec.md` |
| "put the spec in my vault" | Spec note writer | `python3 ~/.golden-path-harness/harness/tools/spec/spec-note.py new --customer <folder> --title "<title>"` |
| "mark the spec agreed" / "it is built" | Front-matter update | `python3 ~/.golden-path-harness/harness/tools/spec/spec-note.py set --customer <folder> --slug <slug> --field status=agreed` |
| "is there already a spec for this?" | Listing | `python3 ~/.golden-path-harness/harness/tools/spec/spec-note.py list --customer <folder>` |
| "record the decision behind it" | Vegviser, not here | the `vegviser-adr` skill and `50-standards/architecture/ADR Standard.md` |

## Where it writes

`<vault>/<customer>/specs/<slug>.md`, from `templates/spec.md`. The vault root comes from `--vault` or
`HARNESS_VAULT`; without either, the tool refuses rather than guessing. `<customer>` is the top-level vault
folder for that customer or product and must already exist — the harness hardcodes no customer name (SEC.2).

A target that leaves the resolved vault root is refused, including through a `..`, a path separator in a name,
or a symlinked folder. An existing note is never overwritten without `--force`, so running `new` twice is
safe: the second run exits 2 and changes nothing. `set` only replaces front-matter keys the note already has.

Exit codes: 0 done, 1 refused, 2 the note exists.
