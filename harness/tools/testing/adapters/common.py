"""Shared plumbing for run_candidate.py agent adapters. An adapter launches one agent CLI, writes its raw
event stream to the trace directory and writes usage.json when the provider reports usage."""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--trace-dir", required=True)
    parser.add_argument("--model", required=True, help="exact model ID; never defaulted or substituted")
    parser.add_argument("--executable", help="override the CLI to launch (tests)")
    parser.add_argument("--deny-path", action="append", default=[], help="absolute path the agent must not read")
    parser.add_argument("--sandbox", help="Codex sandbox mode; default workspace-write. Use danger-full-access only "
                        "inside the evaluation container, which is the isolation boundary")
    return parser.parse_args()


def resolve(executable, default):
    """Command prefix that launches the CLI; a .py override runs under this interpreter (tests)."""
    if executable and executable.endswith(".py"):
        return [sys.executable, executable]
    found = shutil.which(executable or default)
    if not found:
        sys.exit(f"{executable or default} is not installed or not on PATH")
    return [found]


def stream(command, args, name):
    """Run the CLI with the prompt on stdin; return (exit code, parsed JSON events)."""
    trace = pathlib.Path(args.trace_dir)
    prompt = pathlib.Path(args.prompt_file).read_bytes()
    events = []
    with open(trace / f"{name}-events.jsonl", "wb") as raw, open(trace / f"{name}-stderr.txt", "wb") as err:
        process = subprocess.Popen(command, cwd=args.workspace, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err)
        process.stdin.write(prompt)
        process.stdin.close()
        for line in process.stdout:
            raw.write(line)
            raw.flush()
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        process.wait()
    return process.returncode, events


def write_usage(args, usage):
    (pathlib.Path(args.trace_dir) / "usage.json").write_text(json.dumps(usage), encoding="utf-8")


def drive_form(path):
    """/d/x style used by Claude Code path rules."""
    p = (pathlib.PureWindowsPath(path) if len(str(path)) > 1 and str(path)[1] == ":" else pathlib.Path(path)).as_posix()
    return "/" + p[0].lower() + p[2:] if len(p) > 2 and p[1] == ":" else p
