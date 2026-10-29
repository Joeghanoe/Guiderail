"""Grader validation control only. Never include this implementation in a candidate workspace."""
import hashlib
import json
import pathlib
import shutil
import sys
from datetime import datetime, timedelta


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(request, defect):
    op = request["operation"]
    if op == "schedule":
        due = request["last_success_at"] is None or request["last_success_at"][:10] < request["now"][:10]
        return {"status": "succeeded", "due": not due if defect == "schedule" else due}
    if op == "retention":
        now = datetime.fromisoformat(request["now"].replace("Z", "+00:00"))
        eligible = [p["id"] for p in request["points"] if
                    datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
                    + timedelta(days=request["retention_days"], seconds=1 if defect == "retention" else 0) <= now]
        return {"status": "succeeded", "eligible": eligible}
    store = pathlib.Path(request["store"])
    point = store / request["run_id"]
    manifest = point / "manifest.json"
    if op == "backup":
        if manifest.exists() and defect != "versions":
            return {"status": "rejected"}
        point.mkdir(parents=True, exist_ok=True)
        sources, hashes, artifacts = [], {}, []
        count = size = 0
        for source in request["sources"]:
            origin = pathlib.Path(source["path"])
            failed = source.get("fault") == "read" or not origin.is_dir()
            sources.append({"id": source["id"], "status": "failed" if failed else "succeeded",
                            "code": "READ_FAILED" if failed else None})
            if failed:
                continue
            target = point / "payload" / source["id"]
            shutil.copytree(origin, target, dirs_exist_ok=True)
            for path in target.rglob("*"):
                if path.is_file():
                    key = path.relative_to(point).as_posix()
                    hashes[key] = sha(path)
                    artifacts.append(path.relative_to(store).as_posix())
                    if ".git" not in path.relative_to(target).parts:
                        count += 1
                        size += path.stat().st_size
            if defect == "source-mutation":
                next(p for p in origin.rglob("*") if p.is_file()).write_bytes(b"mutated")
        failed = [s for s in sources if s["status"] == "failed"]
        result = {"status": "partial" if failed else "succeeded", "sources": sources,
                  "run_id": request["run_id"], "restore_point": request["run_id"],
                  "created_at": request["now"], "completed_at": request["now"],
                  "object_count": count, "byte_count": size, "artifacts": artifacts,
                  "health": "degraded" if failed else "healthy",
                  "alerts": [{"run_id": request["run_id"], "source_id": s["id"], "code": s["code"]}
                             for s in failed]}
        if defect == "counts":
            result["byte_count"] += 1
        if defect == "false-success":
            result["status"] = "succeeded"
        if defect == "alerts":
            result["alerts"] = []
        if defect == "leak":
            result["logs"] = [s["fault_message"] for s in request["sources"] if "fault_message" in s]
        if defect == "artifact-escape":
            result["artifacts"] = [str(pathlib.Path(request["sources"][0]["path"]) / "binary")]
        manifest.write_text(json.dumps({"hashes": hashes, "response": result, "sources": request["sources"]}))
        return result
    data = json.loads(manifest.read_text())
    if defect == "source-dependent" and not all(pathlib.Path(s["path"]).exists() for s in data["sources"]):
        return {"status": "failed", "sources": []}
    destination = pathlib.Path(request["destination"])
    if destination.exists() and any(destination.iterdir()):
        if defect == "overwrite":
            (destination / "sentinel").write_text("overwritten")
        return {"status": "rejected", "sources": []}
    destination.mkdir(parents=True, exist_ok=True)
    outcomes = []
    for source in data["response"]["sources"]:
        sid = source["id"]
        files = {key: value for key, value in data["hashes"].items() if key.startswith("payload/" + sid + "/")}
        valid = source["status"] == "succeeded" and all((point / key).is_file() and sha(point / key) == value
                                                       for key, value in files.items())
        if defect == "integrity":
            valid = True
        if valid:
            origin = point / "payload" / sid
            if origin.exists():
                shutil.copytree(origin, destination / sid)
            if defect == "git-history" and (destination / sid / ".git/refs/heads/other").exists():
                (destination / sid / ".git/refs/heads/other").unlink()
        outcomes.append({"id": sid, "status": "succeeded" if valid else "failed",
                         "code": None if valid else "INTEGRITY_FAILED"})
    return {"status": "succeeded" if all(s["status"] == "succeeded" for s in outcomes) else "partial",
            "sources": outcomes}


if __name__ == "__main__":
    defect, request_path, response_path = sys.argv[1:]
    if defect == "malformed":
        pathlib.Path(response_path).write_text("[]")
    else:
        request = json.loads(pathlib.Path(request_path).read_text(encoding="utf-8"))
        pathlib.Path(response_path).write_text(json.dumps(run(request, defect)), encoding="utf-8")
