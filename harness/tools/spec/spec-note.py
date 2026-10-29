#!/usr/bin/env python3
"""Create or update a spec note in the user's Obsidian vault, from templates/spec.md.

The playbook playbooks/write-spec.md decides *what* belongs in a spec. This tool only places the note and
keeps its front matter; it writes no prose of its own.

Layout:  <vault>/<customer>/specs/<slug>.md
         `customer` is the top-level vault folder for that customer or product. The harness never hardcodes
         one, and the folder must already exist: a missing folder is a typo, not a new customer.
Vault:   --vault, else $HARNESS_VAULT. Neither: exit 1 naming both.
Safety:  the target is resolved through symlinks and must stay under the resolved vault root. A customer or
         slug with a path separator, a `..`, a dot-folder or a symlink that leaves the vault is refused.

Commands (each takes --vault and --customer):
  new   --title "<title>" [--slug <slug>] [--work-item <id>] [--owner human:<id>]
        [--source-note "<note>"]... [--tag <tag>]... [--force]
  set   --slug <slug> --field <key>=<value> ...
        Replaces front-matter values that are already in the note; it never adds a key.
  list  the spec notes in that customer folder

Placeholders the tool does not fill stay as `{{...}}`, so the open spots are visible in Obsidian.

Exit: 0 done, 1 refused (bad input, no vault, outside the vault, no such note), 2 the note exists (--force).

Example:
  python3 ~/.harness/tools/spec/spec-note.py new --customer <folder> --title "Partner order sync" \\
      --work-item AB-12 --source-note "AB-12 Analysis" --tag orders
"""

import argparse
import datetime
import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # keep the bundle free of __pycache__ folders

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent.parent / "templates" / "spec.md"
SPECS_DIR = "specs"
COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]*$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def fail(message):
    print(f"spec-note: {message}", file=sys.stderr)
    return 1


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def safe_component(value, what):
    """A single folder or file name, no traversal and no hidden folder."""
    if not value or value in {".", ".."} or value.startswith("."):
        return f"{what} {value!r} is not a name inside the vault"
    if "/" in value or "\\" in value or value != pathlib.PurePosixPath(value).name:
        return f"{what} {value!r} must be a single folder name, not a path"
    if not COMPONENT.match(value):
        return f"{what} {value!r} has characters a vault folder name does not use"
    return None


def resolve_vault(given):
    source = "--vault" if given else "$HARNESS_VAULT"
    value = given or os.environ.get("HARNESS_VAULT", "")
    if not value:
        return None, "no vault: pass --vault <path> or set HARNESS_VAULT to the Obsidian vault root"
    path = pathlib.Path(value).expanduser()
    if not path.is_dir():
        return None, f"vault from {source} is not a folder: {path}"
    return pathlib.Path(os.path.realpath(path)), None


def under(root, target):
    """Resolve `target` through symlinks as far as it exists; return it when it stays under `root`."""
    probe, tail = target, []
    while not probe.exists():
        if probe == probe.parent:
            return None
        tail.insert(0, probe.name)
        probe = probe.parent
    final = pathlib.Path(os.path.realpath(probe)).joinpath(*tail)
    try:
        final.relative_to(root)
    except ValueError:
        return None
    return final


def specs_folder(args):
    """(vault root, the `specs` folder in the customer folder), or (None, error message)."""
    vault, error = resolve_vault(args.vault)
    if error:
        return None, error
    error = safe_component(args.customer, "customer folder")
    if error:
        return None, error
    if not (vault / args.customer).is_dir():
        return None, (f"no folder {args.customer!r} in the vault: open the vault and check the name, "
                      "or name the folder this work belongs to")
    customer = under(vault, vault / args.customer)
    if customer is None:
        return None, f"{vault / args.customer} leaves the vault {vault}; refusing to write outside it"
    folder = under(vault, customer / SPECS_DIR)
    if folder is None:
        return None, f"{customer / SPECS_DIR} leaves the vault {vault}; refusing to write outside it"
    return (vault, folder), None


def locate(args, slug):
    """The note's path inside the vault, or an error message."""
    where, error = specs_folder(args)
    if error:
        return None, error
    vault, folder = where
    if not SLUG.match(slug or ""):
        return None, f"slug {slug!r} is not a-z, 0-9 and hyphens (pass --slug)"
    note = under(vault, folder / f"{slug}.md")
    if note is None:
        return None, f"{folder / slug}.md resolves outside the vault {vault}"
    return note, None


def render(args, slug):
    text = TEMPLATE.read_text(encoding="utf-8")
    notes = [n.strip() for n in (args.source_note or []) if n.strip()]
    for line in [l for l in text.splitlines() if "{{source_note}}" in l]:
        indent = line[:len(line) - len(line.lstrip())]
        filled = "\n".join(f'{indent}- "[[{n}]]"' for n in notes) if notes else f"{indent}# {line.strip()}"
        text = text.replace(line, filled)
    tags = ["spec"] + [t for t in (slugify(t) for t in args.tag or []) if t]
    for key, value in {"title": args.title, "slug": slug, "date": datetime.date.today().isoformat(),
                       "work_item": args.work_item, "owner": args.owner,
                       "tags": ", ".join(dict.fromkeys(tags))}.items():
        if value:
            text = text.replace("{{" + key + "}}", value)
    return text


def cmd_new(args):
    note, error = locate(args, args.slug or slugify(args.title))
    if error:
        return fail(error)
    if note.exists() and not args.force:
        print(f"spec-note: {note} exists; edit it, or pass --force to replace it", file=sys.stderr)
        return 2
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(render(args, note.stem), encoding="utf-8")
    print(note)
    return 0


def cmd_set(args):
    note, error = locate(args, args.slug)
    if error:
        return fail(error)
    if not note.is_file():
        return fail(f"no spec at {note}: create it with `new` first")
    pairs = {}
    for field in args.field:
        key, separator, value = field.partition("=")
        if not separator or not key.strip() or "\n" in value:
            return fail(f"--field {field!r} is not <key>=<value>")
        pairs[key.strip()] = value.strip()
    lines = note.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return fail(f"{note} has no front matter to change")
    end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
    if end is None:
        return fail(f"{note} has no front matter to change")
    for key, value in pairs.items():
        hits = [i for i in range(1, end) if lines[i].split(":", 1)[0].strip() == key]
        if not hits:
            return fail(f"{note} has no front-matter key {key!r}; this tool does not add one")
        comment = re.search(r"\s+#.*$", lines[hits[0]].rstrip("\n"))
        lines[hits[0]] = f"{key}: {value}{comment.group(0) if comment else ''}\n"
    note.write_text("".join(lines), encoding="utf-8")
    print(note)
    return 0


def cmd_list(args):
    where, error = specs_folder(args)
    if error:
        return fail(error)
    _, folder = where
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        print(path)
    return 0


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", help="Obsidian vault root; defaults to $HARNESS_VAULT")
    common.add_argument("--customer", required=True, help="top-level vault folder this work belongs to")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", parents=[common], help="create the spec note from templates/spec.md")
    new.add_argument("--title", required=True)
    new.add_argument("--slug", help="file name without .md; derived from the title by default")
    new.add_argument("--work-item", help="tracker id, or `none - <the question the user answered>`")
    new.add_argument("--owner", help="who decides what done means, as human:<id>")
    new.add_argument("--source-note", action="append", help="vault note to link as [[wikilink]]; repeatable")
    new.add_argument("--tag", action="append", help="extra tag besides `spec`; repeatable")
    new.add_argument("--force", action="store_true", help="replace an existing spec note")
    new.set_defaults(run=cmd_new)
    edit = sub.add_parser("set", parents=[common], help="change front-matter values the note already has")
    edit.add_argument("--slug", required=True)
    edit.add_argument("--field", action="append", required=True, metavar="KEY=VALUE")
    edit.set_defaults(run=cmd_set)
    listing = sub.add_parser("list", parents=[common], help="the spec notes in that folder")
    listing.set_defaults(run=cmd_list)
    args = parser.parse_args()
    if not TEMPLATE.is_file():
        return fail(f"no template at {TEMPLATE}")
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
