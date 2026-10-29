#!/usr/bin/env python3
"""Copy an explicit evaluation artifact list and verify its content hashes before a run."""
import argparse
import hashlib
import json
import pathlib
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(value):
    path = pathlib.Path(value)
    if not value or path.is_absolute() or path.drive or ".." in path.parts or path == pathlib.Path("."):
        raise ValueError("artifact path must be a nonempty relative path without traversal")
    if path.as_posix().casefold() == "freeze.json":
        raise ValueError("freeze.json is reserved")
    return path


def freeze(spec, out):
    out = pathlib.Path(out).resolve()
    if out.exists():
        raise ValueError("freeze output already exists; never overwrite a frozen evaluation")
    if not spec.get("approval") or not spec.get("files"):
        raise ValueError("approval reference and explicit files are required")
    entries, names = [], set()
    for entry in spec["files"]:
        source = pathlib.Path(entry["source"]).resolve(strict=True)
        target = relative(entry["path"])
        name = target.as_posix().casefold()
        if name in names or not source.is_file():
            raise ValueError("duplicate artifact path or non-file source")
        names.add(name)
        entries.append((source, target))
    for _, path in entries:
        if any(parent.as_posix().casefold() in names for parent in path.parents):
            raise ValueError("artifact file/directory collision")
    out.mkdir(parents=True)
    hashes = {}
    for source, relative_path in entries:
        target = out / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[relative_path.as_posix()] = sha(target)
    manifest = {"schema_version": 1, "approval": spec["approval"],
                "harness_commit": spec["harness_commit"], "files": hashes,
                "isolation": "hash verification only; not filesystem access control"}
    (out / "freeze.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify(root, expected_manifest_sha=None):
    root = pathlib.Path(root).resolve()
    if expected_manifest_sha is not None and sha(root / "freeze.json") != expected_manifest_sha:
        return ["freeze.json"]
    manifest = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    errors = []
    for name, expected in manifest["files"].items():
        path = root / relative(name)
        if not path.resolve().is_relative_to(root) or not path.is_file() or sha(path) != expected:
            errors.append(name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    errors.extend(sorted(actual - set(manifest["files"]) - {"freeze.json"}))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--spec", help="JSON approval reference, harness_commit and explicit source/path files")
    group.add_argument("--verify", help="existing frozen directory")
    parser.add_argument("--out", help="new freeze directory")
    parser.add_argument("--manifest-sha256", help="trusted manifest hash held outside the frozen directory")
    args = parser.parse_args()
    if args.verify:
        if not args.manifest_sha256:
            parser.error("--verify requires the independently retained --manifest-sha256")
        errors = verify(args.verify, args.manifest_sha256)
        print(json.dumps({"verified": not errors, "mismatches": errors}))
        return 1 if errors else 0
    if not args.out:
        parser.error("--out is required with --spec")
    freeze(json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8")), args.out)
    print(json.dumps({"frozen": str(pathlib.Path(args.out).resolve()),
                      "manifest_sha256": sha(pathlib.Path(args.out) / "freeze.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
