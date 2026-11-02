# Evaluation image for run_candidate.py: .NET 10 SDK, git, Python, Node and the two agent CLIs, pinned.
# Build with build.sh. The agent runs as the unprivileged user "agent"; its HOME is a dedicated login volume.
ARG DOTNET_IMAGE=mcr.microsoft.com/dotnet/sdk:10.0
FROM ${DOTNET_IMAGE}
ARG NODE_MAJOR=22
ARG CLAUDE_CODE_VERSION
ARG CODEX_VERSION
RUN test -n "$CLAUDE_CODE_VERSION" && test -n "$CODEX_VERSION"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git python3 jq ca-certificates curl gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} @openai/codex@${CODEX_VERSION} \
 && git config --system --add safe.directory '*' \
 && rm -rf /var/lib/apt/lists/*
RUN (getent passwd 1000 | cut -d: -f1 | xargs -r userdel -r || true) \
 && useradd -m -u 1000 agent && mkdir -p /work /trace && chown agent /work /trace
USER agent
ENV HOME=/home/agent DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1
WORKDIR /work
