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
    def __init__(self, command, work, timeout=30, criteria=None):
        self.command = command
        self.work = pathlib.Path(work)
        self.timeout = timeout
        self.calls = []
        self.results = {}
        self.criteria = criteria or [f"F{n:02}" for n in range(1, 11)]

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

    def tree(self, path):
        """Every file and directory under path with a content hash; None when path does not exist."""
        path = pathlib.Path(path)
        if not path.exists():
            return None
        return {p.relative_to(path).as_posix(): (digest(p) if p.is_file() else "dir") for p in sorted(path.rglob("*"))}

    def f11(self):
        f = self.fixture("f11", True)
        r = self.backup(f)
        self.success(r)
        before = self.tree(f.store)
        r = self.invoke({"operation": "status", "store": str(f.store), "run_id": "point-a"})
        self.success(r)
        run = r.get("run", {})
        require(run.get("run_id") == "point-a" and run.get("state") == "succeeded", "status does not name the run and its state")
        require(stamp(run["created_at"]) == stamp(NOW), "status ignores the recorded creation time")
        require({s["id"] for s in run.get("sources", [])} == {s["id"] for s in f.sources}, "status lacks source outcomes")
        require(run.get("object_count") == f.count and run.get("byte_count") == f.size, "status counts differ from the run")
        require(self.tree(f.store) == before, "status call changed the store")
        r = self.invoke({"operation": "status", "store": str(f.store), "run_id": "never-ran"})
        require(r["status"] == "rejected" and r.get("code") == "run_not_found", "unknown run is not reported as not found")
        require(self.tree(f.store) == before, "status of an unknown run changed the store")

    def f12(self):
        f = self.fixture("f12")
        self.success(self.backup(f))
        before = self.tree(f.store)
        r = self.invoke({"operation": "health", "store": str(f.store)})
        self.success(r)
        require(r.get("health") == "healthy", "usable store is not healthy")
        require(self.tree(f.store) == before, "health call wrote to the store")
        broken = f.root / "not-a-directory"
        broken.write_text("a file where a store should be")
        r = self.invoke({"operation": "health", "store": str(broken)})
        require(r["status"] == "failed" and r.get("health") == "unhealthy", "unusable store reported healthy")
        require(broken.read_text() == "a file where a store should be", "health call modified an unusable store")

    def f13(self):
        f = self.fixture("f13", True)
        before = self.tree(f.store)
        r = self.backup(f, dry_run=True)
        self.success(r)
        require(r.get("dry_run") is True and r.get("artifacts") == [], "dry run is not labelled or stored artifacts")
        require(r.get("object_count") == f.count and r.get("byte_count") == f.size, "dry run does not report what it would copy")
        require({s["id"] for s in r.get("sources", [])} == {s["id"] for s in f.sources}, "dry run lacks source outcomes")
        require(self.tree(f.store) == before, "dry run wrote bytes or a recovery point to the store")
        self.success(self.backup(f))

    def f14(self):
        f = self.fixture("f14")
        for source in f.sources:
            if source["id"] == "blob":
                source["exclude"] = ["nested/*", "*.tmp"]
        (f.input / "blob" / "scratch.tmp").write_bytes(b"temporary")
        kept = {p: h for p, h in inventory(f.input).items() if not p.startswith("blob/nested/") and not p.endswith(".tmp")}
        r = self.backup(f)
        self.success(r)
        require(r.get("object_count") == len(kept), "excluded files are counted as backed up")
        excluded = r.get("excluded", [])
        require({(e.get("source_id"), e.get("path")) for e in excluded} == {("blob", "nested/value"), ("blob", "scratch.tmp")},
                "excluded files are not listed with their source")
        require(all(e.get("reason") for e in excluded), "an exclusion has no reason")
        result, dest = self.restore(f)
        self.success(result)
        require(inventory(dest) == kept, "excluded content was stored or included content was lost")
        require(inventory(f.input) == {**kept, "blob/nested/value": f.expected["blob/nested/value"],
                                       "blob/scratch.tmp": digest(f.input / "blob" / "scratch.tmp")},
                "exclusion modified the source")

    def f15(self):
        names = {"RunStarted", "SourceStarted", "SourceFinished", "RunFinished"}
        allowed = {"event", "run_id", "source_id", "outcome", "code", "object_count", "byte_count", "duration_ms"}
        f, r = self.failure("f15")
        events = r.get("events")
        require(isinstance(events, list) and events, "backup response has no events")
        require(all(e.get("event") in names for e in events), "an event is outside the catalogue")
        require(all(set(e) <= allowed for e in events), "an event carries a property outside the contract")
        require(all(e.get("run_id") == "point-a" for e in events), "an event lacks the run id")
        require([e["event"] for e in events].count("RunStarted") == 1 and events[0]["event"] == "RunStarted", "RunStarted is not first and once")
        require([e["event"] for e in events].count("RunFinished") == 1 and events[-1]["event"] == "RunFinished", "RunFinished is not last and once")
        for source in f.sources:
            sid = source["id"]
            mine = [e["event"] for e in events if e.get("source_id") == sid]
            require(mine == ["SourceStarted", "SourceFinished"], f"source {sid} lacks its started and finished events")
        finished = {e["source_id"]: e for e in events if e["event"] == "SourceFinished"}
        require(all(finished[s].get("outcome") == "failed" and finished[s].get("code") for s in ("missing", "broken")),
                "failed sources are not reported with a code in their finished event")
        require(events[-1].get("outcome") in {"partial", "failed"}, "RunFinished does not carry the run outcome")
        require(f.canary not in json.dumps(events), "an event carries payload content")

    def f16(self):
        f = self.fixture("f16")
        outside = f.root / "outside"
        outside.mkdir()
        (outside / "sentinel").write_text("keep")
        before = self.tree(f.root / "outside")
        for kind, value in (("run_id", "../outside/escape"), ("run_id", str(outside / "abs")), ("run_id", "a/b")):
            r = self.invoke(f.request("backup", sources=f.sources, **{kind: value}))
            require(r["status"] == "rejected", f"hostile {kind} {value!r} was accepted")
            require(self.tree(f.root / "outside") == before, "a hostile run id wrote outside the store")
        hostile = [{**f.sources[0], "id": "../../outside/src"}]
        r = self.invoke(f.request("backup", sources=hostile))
        require(r["status"] == "rejected", "a hostile source id was accepted")
        require(self.tree(f.root / "outside") == before, "a hostile source id wrote outside the store")
        self.success(self.backup(f))
        r = self.invoke(f.request("restore", destination=str(f.root / "restored"), run_id="../outside"))
        require(r["status"] in {"rejected", "failed"}, "a hostile run id was accepted on restore")

    def run(self):
        before = digest(pathlib.Path(__file__))
        for key in self.criteria:
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
        gates = [k for k in ("F03", "F10", "F16") if self.results.get(k, {}).get("status") == "fail"]
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


def scenario_criteria(here):
    """The F-criteria the frozen scenario lists; the original F01-F10 when no scenario file sits beside the grader."""
    path = here.with_name("scenario.json")
    if not path.is_file():
        return None
    ids = json.loads(path.read_text(encoding="utf-8")).get("eval_ids", [])
    return [i for i in ids if i.startswith("F") and i[1:].isdigit()] or None


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
    here = pathlib.Path(__file__).resolve()
    guarded = [here.parent] + [p for p in here.parents if (p / ".git").exists()][:1]
    if any(out.is_relative_to(root) for root in guarded) or args.timeout <= 0:
        parser.error("use an external output directory and positive timeout")
    out.mkdir(parents=True, exist_ok=False)
    report = Grader(command, out, args.timeout, scenario_criteria(here)).run()
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "calls"}, indent=2))
    return 1 if report["status"] == "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
