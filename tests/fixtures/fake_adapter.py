"""Stand-in agent adapter for runner tests. Never a real model."""
import argparse
import json
import pathlib
import shutil
import time

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="ok")
parser.add_argument("--workspace")
parser.add_argument("--prompt-file")
parser.add_argument("--trace-dir")
parser.add_argument("--control")
parser.add_argument("--touch")
parser.add_argument("--python")
args = parser.parse_args()
workspace, trace = pathlib.Path(args.workspace), pathlib.Path(args.trace_dir)
assert (workspace / "TASK.md").is_file()
if args.mode == "sleep":
    time.sleep(60)
if args.touch:
    pathlib.Path(args.touch).write_text("changed", encoding="utf-8")
if args.mode != "no-entrypoint":
    shutil.copyfile(args.control, workspace / "backup_control.py")
    command = [args.python, "{workspace}/backup_control.py", "none"]
    (workspace / "EVAL.json").write_text(json.dumps({"command": command}), encoding="utf-8")
(trace / "usage.json").write_text(json.dumps({"input_tokens": 10, "output_tokens": 5, "cost": None}), encoding="utf-8")
(workspace / "REPORT.md").write_text("done", encoding="utf-8")
