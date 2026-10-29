#!/usr/bin/env python3
"""Independent local backup contract checks. No model/provider SDK or application imports."""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import time
from datetime import datetime, timedelta, timezone

NOW = "2026-10-29T00:00:00Z"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def git(path, *args):
    env = {**os.environ, "GIT_AUTHOR_DATE": NOW, "GIT_COMMITTER_DATE": NOW}
    return subprocess.check_output(["git", "-c", "core.hooksPath=" + str(path / ".no-hooks"),
                                    "-C", str(path), *args], stderr=subprocess.PIPE, env=env).decode().strip()


def inventory(path):
    return {p.relative_to(path).as_posix(): digest(p) for p in path.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(path).parts}


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.utcoffset() == timedelta(0), "timestamp must be UTC")
    return parsed


class Fixture:
    def __init__(self, root, with_git=False):
        self.root = root
        self.input = root / "input"
        self.store = root / "store"
        self.sources = []
        self.expected = {}
        self.refs = None
        self.canary = "SYNTHETIC_PRIVATE_" + hashlib.sha256(root.name.encode()).hexdigest()[:32]
        for name, files in {
            "blob": {"empty": b"", "binary": bytes(range(256)), "nested/value": self.canary.encode()},
            "sql": {"export.sql": b"CREATE TABLE Sample (Id INT); INSERT INTO Sample VALUES (1);"},
            "activity": {"events.json": b'[{"id":"event-1"}]'},
            "deployment": {"logs.json": b'[{"id":"deployment-1"}]'},
            "pipeline": {"runs.json": b'[{"id":"run-1","trigger":"daily"}]'},
        }.items():
            folder = self.input / name
            for relative, content in files.items():
                target = folder / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            self.sources.append({"id": name, "kind": "files", "path": str(folder)})
        if with_git:
            folder = self.input / "repository"
            folder.mkdir()
            git(folder, "init", "-q", "-b", "main")
            for content in ("first", "second"):
                (folder / "sample.txt").write_text(content)
                git(folder, "add", ".")
                git(folder, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-qm", content)
            git(folder, "branch", "other", "HEAD~1")
            git(folder, "tag", "v1", "HEAD~1")
            self.refs = git(folder, "show-ref", "--heads", "--tags")
            self.history = git(folder, "rev-list", "--all", "--parents")
            self.sources.append({"id": "repository", "kind": "git", "path": str(folder)})
        self.expected = inventory(self.input)
        self.count = len(self.expected)
        self.size = sum((self.input / p).stat().st_size for p in self.expected)
        (root / "expected.json").write_text(json.dumps({"files": self.expected, "git_refs": self.refs,
                                                       "object_count": self.count, "byte_count": self.size}),
                                           encoding="utf-8")

    def request(self, operation, **kwargs):
        return {"operation": operation, "store": str(self.store), "run_id": "point-a",
                "now": NOW, "retention_days": 30, **kwargs}

    def verify_restore(self, destination):
        require(inventory(destination) == self.expected, "restored content differs from independent hashes")
        if self.refs is not None:
            repo = destination / "repository"
            require(git(repo, "show-ref", "--heads", "--tags") == self.refs, "Git refs were not preserved")
            require(git(repo, "rev-list", "--all", "--parents") == self.history, "Git history was not preserved")


class Grader:
    def __init__(self, command, work, timeout=30):
        self.command = command
        self.work = pathlib.Path(work)
        self.timeout = timeout
        self.calls = []
        self.results = {}

    def invoke(self, request):
        call_dir = self.work / "calls" / str(len(self.calls))
        call_dir.mkdir(parents=True)
        req, res = call_dir / "request.json", call_dir / "response.json"
        req.write_text(json.dumps(request), encoding="utf-8")
        started = time.monotonic()
        call = {"request": request, "elapsed_seconds": None}
        self.calls.append(call)
        try:
            run = subprocess.run([*self.command, str(req), str(res)], cwd=call_dir,
                                 capture_output=True, timeout=self.timeout)
            stdout = run.stdout.decode("utf-8", errors="replace")
            stderr = run.stderr.decode("utf-8", errors="replace")
            call.update(exit_code=run.returncode, stdout=stdout, stderr=stderr)
            require(run.returncode == 0, "candidate command exited nonzero")
            require(res.is_file(), "candidate did not write a response")
            require(res.stat().st_size <= 1024 * 1024, "response exceeds 1 MiB")
            response = json.loads(res.read_text(encoding="utf-8-sig"))
            require(isinstance(response, dict), "response must be an object")
            require(response.get("status") in {"succeeded", "partial", "failed", "rejected"}, "invalid status")
            call["response"] = response
            return response
        finally:
            call["elapsed_seconds"] = time.monotonic() - started

    def fixture(self, name, with_git=False):
        root = self.work / name
        root.mkdir()
        return Fixture(root, with_git)

    def backup(self, f, **kwargs):
        return self.invoke(f.request("backup", sources=f.sources, **kwargs))

    def restore(self, f, label="restored", **kwargs):
        dest = f.root / label
        result = self.invoke(f.request("restore", destination=str(dest), **kwargs))
        return result, dest

    def success(self, result):
        require(result.get("status") == "succeeded", "operation did not succeed")

    def f01(self):
        f = self.fixture("f01", True)
        self.success(self.backup(f))
        result, dest = self.restore(f)
        self.success(result)
        f.verify_restore(dest)

    def f02(self):
        f = self.fixture("f02", True)
        self.success(self.backup(f))
        require(f.input.resolve() == (f.root.resolve() / "input") and not f.input.is_symlink(),
                "fixture input path changed before removal")
        # Only generated inputs are removed; expectations are already held independently in memory.
        def remove_readonly(function, path, error):
            if not isinstance(error, PermissionError) or not pathlib.Path(path).resolve().is_relative_to(f.input.resolve()):
                raise error
            os.chmod(path, stat.S_IWRITE)
            function(path)
        shutil.rmtree(f.input, onexc=remove_readonly)
        result, dest = self.restore(f)
        self.success(result)
        f.verify_restore(dest)

    def f03(self):
        f = self.fixture("f03")
        self.success(self.backup(f))
        require(inventory(f.input) == f.expected, "backup modified source contents")
        dest = f.root / "occupied"
        dest.mkdir()
        (dest / "sentinel").write_text("preserve me")
        before = inventory(dest)
        response = self.invoke(f.request("restore", destination=str(dest)))
        require(response["status"] in {"failed", "rejected"}, "occupied restore destination was accepted")
        require(inventory(dest) == before, "restore modified occupied destination")
        require(inventory(f.input) == f.expected, "restore modified source contents")

    def failure(self, name):
        f = self.fixture(name)
        f.sources += [{"id": "missing", "kind": "files", "path": str(f.input / "absent")},
                      {"id": "broken", "kind": "files", "path": str(f.input / "blob"),
                       "fault": "read", "fault_message": f.canary}]
        r = self.backup(f)
        require(r["status"] in {"partial", "failed"}, "incomplete backup reported success")
        outcomes = r.get("sources", [])
        require(len(outcomes) == len(f.sources), "missing or duplicate source outcomes")
        by_id = {s["id"]: s for s in outcomes}
        require(set(by_id) == {s["id"] for s in f.sources}, "source IDs differ")
        for source in f.sources:
            outcome = by_id[source["id"]]
            if source["id"] in {"missing", "broken"}:
                require(outcome["status"] == "failed" and outcome.get("code"), "failed source not identified")
            else:
                require(outcome["status"] == "succeeded", "healthy source did not complete")
        return f, r

    def f04(self):
        f, _ = self.failure("f04")
        # Verify healthy results independently, rather than trusting source status fields.
        _, dest = self.restore(f)
        for path, expected in f.expected.items():
            require((dest / path).is_file() and digest(dest / path) == expected, "healthy source was not backed up")

    def f05(self):
        f = self.fixture("f05", True)
        self.success(self.backup(f))
        original = dict(f.expected)
        (f.input / "blob/binary").write_bytes(b"changed revision")
        newer = inventory(f.input)
        self.success(self.backup(f, run_id="point-b"))
        duplicate = self.backup(f)
        require(duplicate["status"] in {"succeeded", "rejected", "failed"}, "ambiguous duplicate result")
        for point, expected in (("point-a", original), ("point-b", newer)):
            result, dest = self.restore(f, label=point, run_id=point)
            self.success(result)
            f.expected = expected
            f.verify_restore(dest)

    def f06(self):
        for last, now, due in ((None, NOW, True), (NOW, NOW, False),
                               ("2026-10-28T23:59:59Z", NOW, True),
                               (NOW, "2026-10-29T23:59:59Z", False)):
            r = self.invoke({"operation": "schedule", "now": now, "last_success_at": last})
            self.success(r)
            require(r.get("due") is due, "daily scheduling boundary is incorrect")
        for now, expected in (("2026-11-27T23:59:59Z", []), ("2026-11-28T00:00:00Z", ["p"]),
                              ("2026-11-28T00:00:01Z", ["p"])):
            r = self.invoke({"operation": "retention", "now": now, "retention_days": 30,
                             "points": [{"id": "p", "created_at": NOW}]})
            self.success(r)
            require(r.get("eligible") == expected, "retention boundary is incorrect")

    def f07(self):
        for damage in ("corrupt", "missing"):
            f = self.fixture("f07-" + damage)
            r = self.backup(f)
            self.success(r)
            paths = r.get("artifacts")
            require(isinstance(paths, list) and paths, "no payload artifacts exposed for integrity testing")
            relative = pathlib.Path(paths[0])
            require(not relative.is_absolute(), "artifact must be relative")
            target = (f.store / relative).resolve()
            require(target.is_relative_to(f.store.resolve()) and target.is_file(), "artifact outside store or missing")
            if damage == "missing":
                target.unlink()
            else:
                target.write_bytes(b"corrupted-by-independent-grader")
            r, _ = self.restore(f)
            require(r["status"] in {"failed", "partial"}, "damaged backup reported successful restore")
            require(any(s.get("status") == "failed" and s.get("code") for s in r.get("sources", [])),
                    "damaged source was not reported failed")

    def f08(self):
        f = self.fixture("f08", True)
        r = self.backup(f)
        self.success(r)
        require(r.get("run_id") == "point-a" and r.get("restore_point") == "point-a", "recovery point missing")
        require(stamp(r["created_at"]) == stamp(NOW), "creation time ignores supplied clock")
        require(stamp(r["completed_at"]) >= stamp(r["created_at"]), "completion precedes creation")
        require(type(r.get("object_count")) is int and r["object_count"] == f.count, "incorrect object count")
        require(type(r.get("byte_count")) is int and r["byte_count"] == f.size, "incorrect byte count")
        outcomes = r.get("sources", [])
        require(len(outcomes) == len(f.sources) and {s["id"] for s in outcomes} == {s["id"] for s in f.sources},
                "incorrect source report")
        require(all(s["status"] == "succeeded" for s in outcomes), "incorrect successful source outcome")

    def f09(self):
        _, r = self.failure("f09")
        require(r.get("health") in {"degraded", "unhealthy"}, "partial failure is not observable")
        for source in ("missing", "broken"):
            require(any(a.get("source_id") == source and a.get("run_id") == "point-a" and a.get("code")
                        for a in r.get("alerts", [])), "failed source has no correlated alert")
        f = self.fixture("f09-healthy")
        r = self.backup(f)
        require(r.get("health") == "healthy" and r.get("alerts") == [], "healthy run reports false alert")

    def f10(self):
        start = len(self.calls)
        f, _ = self.failure("f10")
        self.restore(f)
        for call in self.calls[start:]:
            operational = json.dumps({k: v for k, v in call.items() if k in {"stdout", "stderr", "response"}})
            require(f.canary not in operational, "synthetic private payload leaked to operational output")

    def run(self):
        before = digest(pathlib.Path(__file__))
        for number in range(1, 11):
            key = f"F{number:02}"
            try:
                getattr(self, key.lower())()
                self.results[key] = {"status": "pass"}
            except OSError as ex:
                self.results[key] = {"status": "inconclusive", "reason": "execution environment: " + str(ex)}
            except (AssertionError, KeyError, TypeError, ValueError, AttributeError, subprocess.SubprocessError) as ex:
                self.results[key] = {"status": "fail", "reason": str(ex)}
        statuses = {r["status"] for r in self.results.values()}
        functional = "fail" if "fail" in statuses else "inconclusive" if "inconclusive" in statuses else "pass"
        tampered = before != digest(pathlib.Path(__file__))
        gates = [k for k in ("F03", "F10") if self.results[k]["status"] == "fail"]
        if tampered:
            gates.append("grader-modified")
        return {"schema_version": 1, "grader_sha256": before, "functional_status": functional,
                "status": "fail" if functional == "fail" or gates else "inconclusive",
                "checks": self.results, "hard_gate_violations": gates,
                "policy": {"status": "inconclusive", "reason": "subprocess execution does not enforce isolation or observe all tools"},
                "architecture": {"status": "inconclusive", "reason": "run build and CODE.5 separately"},
                "behavior": {"status": "inconclusive", "reason": "candidate model tool trace required"},
                "cost": None, "tokens": None, "usage_reason": "provider usage is external run metadata",
                "calls": self.calls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True, help="JSON array of executable argv with absolute paths")
    parser.add_argument("--out", required=True, help="new external evidence directory")
    parser.add_argument("--timeout", type=int, default=30, help="per-operation timeout; not the model run budget")
    args = parser.parse_args()
    command = json.loads(args.command)
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        parser.error("command must be a nonempty JSON string array")
    out = pathlib.Path(args.out).resolve()
    repository = pathlib.Path(__file__).resolve().parents[3]
    if out.is_relative_to(repository) or args.timeout <= 0:
        parser.error("use an external output directory and positive timeout")
    out.mkdir(parents=True, exist_ok=False)
    report = Grader(command, out, args.timeout).run()
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "calls"}, indent=2))
    return 1 if report["status"] == "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
