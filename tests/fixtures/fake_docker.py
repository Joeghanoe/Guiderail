"""Stand-in for the docker CLI: logs each call and runs the container command on the host, mapping mounts."""
import json
import os
import pathlib
import subprocess
import sys

argv = sys.argv[1:]
log = pathlib.Path(os.environ["FAKE_DOCKER_LOG"])


def record(entry):
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


if argv[:2] == ["image", "inspect"]:
    sys.exit(1 if os.environ.get("FAKE_DOCKER_NO_IMAGE") else (print("sha256:fake") or 0))
if argv[:2] == ["volume", "inspect"]:
    sys.exit(0)
if argv[0] == "kill":
    record({"kill": argv[1]})
    sys.exit(0)

assert argv[0] == "run"
mounts, env, flags, workdir, name, network = [], {}, [], "/", None, None
i = 1
while argv[i].startswith("-"):
    flag = argv[i]
    if flag in {"--rm", "-it"}:
        i += 1
    elif flag == "-v":
        host, inner, mode = argv[i + 1].rsplit(":", 2)
        mounts.append((host, inner, mode))
        i += 2
    elif flag == "-e":
        key, value = argv[i + 1].split("=", 1)
        env[key] = value
        i += 2
    else:
        value = argv[i + 1]
        flags.append([flag, value])
        if flag == "--name":
            name = value
        if flag == "-w":
            workdir = value
        if flag == "--network":
            network = value
        i += 2
image, command = argv[i], argv[i + 1:]
record({"name": name, "network": network, "mounts": mounts, "flags": [f[0] for f in flags], "image": image})


def host(value):
    for source, inner, _ in sorted(mounts, key=lambda m: -len(m[1])):
        value = value.replace(inner, source.replace("\\", "/"))
    return value


mapped = [sys.executable if part == "python3" else host(part) for part in command]
run = subprocess.run(mapped, cwd=host(workdir) if workdir != "/" else None, env={**os.environ, **env})
sys.exit(run.returncode)
