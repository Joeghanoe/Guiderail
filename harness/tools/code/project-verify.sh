#!/usr/bin/env bash
# The quick verify command of one project, kept outside the repo (T.1). CI is the authority and runs the full gate; this
# command is the agent's fast local subset, so the repo carries no second copy of the pipeline.
#
# Usage:  project-verify.sh path [repo-root]
#           prints ~/.golden-path-harness/projects/<repo-id>/verify.sh (whether or not it exists yet)
#         project-verify.sh init [--profile generic|service|web-app] [repo-root]
#           writes it from the template; never overwrites one that exists
# The repo-id comes from the origin URL (host, organisation, project and repo), or the folder name and a hash of its path when
# there is no remote. GOLDEN_PATH_HOME overrides ~/.golden-path-harness.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
home="${GOLDEN_PATH_HOME:-$HOME/.golden-path-harness}"

repo_root() { git -C "${1:-.}" rev-parse --show-toplevel 2>/dev/null || (cd "${1:-.}" && pwd); }

repo_id() { # repo_id <root>
  local url
  url="$(git -C "$1" remote get-url origin 2>/dev/null || true)"
  if [[ -n "$url" ]]; then
    sed -E 's#^[A-Za-z+]+://([^@/]*@)?##; s#^[^@/]+@##; s#:#/#; s#\.git$##; s#/+$##; s#[^A-Za-z0-9._/-]#_#g; s#/#__#g' <<<"$url"
  else
    printf '%s-%s' "$(basename "$1")" "$(printf %s "$1" | shasum | cut -c1-8)"
  fi
}

verify_path() { # verify_path <root>
  printf '%s/projects/%s/verify.sh\n' "$home" "$(repo_id "$1")"
}

cmd="${1:-}"
shift || true
case "$cmd" in
  path)
    verify_path "$(repo_root "${1:-.}")"
    ;;
  init)
    profile=generic
    if [[ "${1:-}" == "--profile" ]]; then
      profile="${2:?--profile needs generic, service or web-app}"
      shift 2
    fi
    case "$profile" in generic | service | web-app) ;; *) echo "project-verify: unknown profile '$profile'" >&2; exit 1 ;; esac
    target="$(verify_path "$(repo_root "${1:-.}")")"
    if [[ -e "$target" ]]; then
      echo "kept     $target (exists)"
    else
      mkdir -p "$(dirname "$target")"
      cp "$here/templates/repo/scripts/verify.sh" "$target"
      chmod +x "$target"
      sed -i.bak "s/^DESIGN_PROFILE=.*/DESIGN_PROFILE=$profile/" "$target" && rm -f "$target.bak"
      echo "created  $target"
    fi
    ;;
  *)
    echo "usage: project-verify.sh path [repo-root] | init [--profile generic|service|web-app] [repo-root]" >&2
    exit 1
    ;;
esac
