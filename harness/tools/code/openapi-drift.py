#!/usr/bin/env python3
"""DEL.5: fail when a committed OpenAPI snapshot no longer matches the document the build generates.

Usage: openapi-drift.py --generated <fresh.json> --committed <snapshot.json> [--ignore-version]
Both files are OpenAPI 3 JSON. They are compared after normalisation (keys sorted, whitespace ignored), so only a real change fails.
Prints the operations added and removed (`GET /path`) and how many other parts changed, then how to refresh the snapshot.
Exit 0 when equal, 1 when they differ or a file cannot be read. Reads files only.
"""
import argparse
import json
import pathlib
import sys

METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def load(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        print(f"openapi-drift: cannot read {path}: {error}", file=sys.stderr)
        sys.exit(1)


def operations(doc):
    found = set()
    for route, item in (doc.get("paths") or {}).items():
        if isinstance(item, dict):
            found |= {f"{method.upper()} {route}" for method in item if method.lower() in METHODS}
    return found


def normalise(doc, ignore_version):
    doc = json.loads(json.dumps(doc))
    if ignore_version and isinstance(doc.get("info"), dict):
        doc["info"].pop("version", None)
    return json.dumps(doc, sort_keys=True, separators=(",", ":"))


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--generated", required=True)
    parser.add_argument("--committed", required=True)
    parser.add_argument("--ignore-version", action="store_true", help="do not fail when only info.version differs")
    args = parser.parse_args(argv)
    generated, committed = load(args.generated), load(args.committed)
    if normalise(generated, args.ignore_version) == normalise(committed, args.ignore_version):
        print("openapi-drift: the committed snapshot matches the generated document")
        return 0
    added = sorted(operations(generated) - operations(committed))
    removed = sorted(operations(committed) - operations(generated))
    for line in added:
        print(f"added:   {line}")
    for line in removed:
        print(f"removed: {line}  (a breaking change for callers)")
    if not added and not removed:
        print("changed: the operations are the same; parameters, schemas, responses or metadata differ")
    print("openapi-drift: the snapshot is stale. Regenerate it with the build, review the diff, and commit it.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
