#!/usr/bin/env bash
# Build the evaluation image. Pin the CLI versions you want to evaluate; defaults are what this machine runs.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-harness-eval:local}"
claude_version="${CLAUDE_CODE_VERSION:-$(claude --version 2>/dev/null | awk '{print $1}')}"
codex_version="${CODEX_VERSION:-$(codex --version 2>/dev/null | awk '{print $2}')}"
docker build -t "$tag" \
  --build-arg CLAUDE_CODE_VERSION="${claude_version:?set CLAUDE_CODE_VERSION}" \
  --build-arg CODEX_VERSION="${codex_version:?set CODEX_VERSION}" "$here"
docker image inspect --format 'image id: {{.Id}}' "$tag"
