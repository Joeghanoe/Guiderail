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
place "$templates/repo/scripts/verify.sh" scripts/verify.sh
chmod +x "$target/scripts/verify.sh"
mkdir -p "$target/docs/adr"

# The gate profile and the harness location are written into the repo's verify command.
sed -i.bak "s/^DESIGN_PROFILE=.*/DESIGN_PROFILE=$profile/" "$target/scripts/verify.sh" && rm -f "$target/scripts/verify.sh.bak"

cat <<EOF

Next, before any file under src/:
  1. Fill docs/solution-design.md: every heading, no template prompt left (DEL.4).
  2. Write one ADR per hard-to-reverse decision in docs/adr/NNNN-title.md: context, decision, consequences.
  3. Fill AGENTS.md: layout, vocabulary, decisions, change map, verifying, when to ask.
  4. Run: bash scripts/verify.sh --design
     It must say "pass" before you create any file under src/. Do not write code first and the design after.
  5. Build, then run scripts/verify.sh. It fails while the design is unfinished or the code does not follow it, and it
     must pass before you call the work done (T.1). Gate profile: $profile.
EOF
