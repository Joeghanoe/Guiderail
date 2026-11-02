"""Stand-in agent for brownfield runner tests: edits one snapshot file, optionally leaking a credential."""
import argparse
import pathlib

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="ok")
parser.add_argument("--workspace")
parser.add_argument("--prompt-file")
parser.add_argument("--trace-dir")
args = parser.parse_args()
workspace = pathlib.Path(args.workspace)
assert (workspace / "TASK.md").is_file()
assert not list(workspace.rglob("criteria.md")), "criteria must never reach the candidate"
if args.mode != "noop":
    target = workspace / "Services" / ("Thing.cs" if args.mode == "twotypes" else "Added.cs")
    text = target.read_text(encoding="utf-8") if target.exists() else "namespace Demo;\n"
    text += "\npublic class Added { }\n"
    if args.mode == "secret":
        text += '// Password=hunter2hunter2\n'
    target.write_text(text, encoding="utf-8")
