#!/usr/bin/env bash
# Start a new repo or service design-first (DEL.4): write the files a new repo owns into the current directory,
# for you to fill in, and say what to do next. Never overwrites a file that exists.
# Usage: bash greenfield-init.sh [--service | --web-app] [target-dir]   (run through bash: copies do not always keep the exec bit)
#   --web-app  the repo is an HTTP application that talks to other systems: ports for each of them (CODE.8) under any names,
#              an error-code catalogue and a health endpoint (OBS.1, OBS.3), without the run, source and store roles of a service.
#   --service  the repo is a service that runs operations and reports them: the verify gate also checks the
#              CODE.8 source/store interfaces and the OBS.3 event and error-code contract.
set -euo pipefail

profile=generic
case "${1:-}" in
  --service) profile=service; shift ;;
  --web-app) profile=web-app; shift ;;
esac
target="${1:-.}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
templates="$here/templates"

place() { # place <from> <to>
  if [[ -e "$target/$2" ]]; then
    echo "kept     $2 (exists)"
  else
    mkdir -p "$(dirname "$target/$2")"
    cp "$1" "$target/$2"
    echo "created  $2"
  fi
}

place "$templates/solution-design.md" docs/solution-design.md
place "$templates/repo/AGENTS.md" AGENTS.md
mkdir -p "$target/docs/adr"

# The quick verify command is the agent's, not the repo's: it goes to ~/.golden-path-harness/projects/<repo-id>/ (T.1), with the
# gate profile written into it. CI is the authority; the repo gets no second copy of the pipeline.
bash "$here/tools/code/project-verify.sh" init --profile "$profile" "$target"
verify="$(bash "$here/tools/code/project-verify.sh" path "$target")"

cat <<EOF

Next, before any file under src/:
  1. Fill docs/solution-design.md: every heading, no template prompt left (DEL.4).
  2. Write one ADR per hard-to-reverse decision in docs/adr/NNNN-title.md: context, decision, consequences.
  3. Fill AGENTS.md: layout, vocabulary, decisions, change map, verifying, when to ask.
  4. Run: bash $verify --design
     It must say "pass" before you create any file under src/. Do not write code first and the design after.
  5. Build, then run $verify. It fails while the design is unfinished or the code does not follow it, and it
     must pass before you call the work done (T.1). Gate profile: $profile.
  6. CI is the authority. Propose the design gate (design-check.py) as a step in the repo's pipeline, as a diff for a human (CLD.2).
EOF
