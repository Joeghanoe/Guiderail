#!/usr/bin/env python3
"""Mine pull request review threads from an Azure DevOps project into an anonymised CSV.

Use: find recurring reviewer feedback, then distill it into cases and eval scenarios (H.1, H.2).
Read-only: only GET requests through `az rest`. Run it yourself, logged in with `az login`.

One row per review thread whose root comment is by --author (default: every author). Names, emails,
identity mentions, URLs and token-like strings are scrubbed; other people become "colleague-N".
The CSV still contains code and prose from your repos: keep it outside git (default: ~/.harness-feedback/mined/).

Usage:
  ado-mine-review-comments.py --org https://dev.azure.com/<org> --project "<project>" --author "Joost-Jan"
  ado-mine-review-comments.py ... --author ""        # all authors
  ado-mine-review-comments.py ... --years 1 --repo MyRepo
  ado-mine-review-comments.py ... --redact "Anna,Bob"   # names that appear in text but not on the PR

Columns: repo, pr_id, pr_created, pr_status, thread_rank_in_pr, is_first_thread_in_pr, thread_status,
file, line_from, line_to, comment, replies, reply_count
"""
import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ADO_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798"  # Azure DevOps AAD application id
API = "api-version=7.1"
PAGE = 100

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
MENTION = re.compile(r"@<[0-9A-Fa-f-]{36}>")
GUID = re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b")
URL = re.compile(r"https?://\S+")
TOKENISH = re.compile(r"\b(?:[A-Za-z0-9+/_-]{32,}={0,2}|[0-9a-fA-F]{20,})\b")


def az_get(url: str):
    cmd = ["az", "rest", "--method", "get", "--resource", ADO_RESOURCE, "--url", url, "--output", "json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"az rest failed for {url}\n{res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def list_pull_requests(base: str, since: datetime, repo: str | None):
    prs, skip = [], 0
    while True:
        q = {
            "searchCriteria.status": "all",
            "searchCriteria.minTime": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "searchCriteria.queryTimeRangeType": "created",
            "$top": PAGE,
            "$skip": skip,
        }
        page = az_get(f"{base}/_apis/git/pullrequests?{urllib.parse.urlencode(q)}&{API}").get("value", [])
        prs += page
        print(f"  listed {len(prs)} pull requests", file=sys.stderr)
        if len(page) < PAGE:
            break
        skip += PAGE
    if repo:
        prs = [p for p in prs if p["repository"]["name"].lower() == repo.lower()]
    return prs


def get_threads(base: str, pr: dict):
    repo_id, pr_id = pr["repository"]["id"], pr["pullRequestId"]
    return az_get(f"{base}/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}/threads?{API}").get("value", [])


class Scrubber:
    """Per pull request: map every identity to a stable role and strip names from the text."""

    def __init__(self, author_match: str, extra_names=()):
        self.author_match = author_match.lower()
        self.roles: dict[str, str] = {}
        # Names that are mentioned in the text but are not on the pull request (colleagues, customers).
        self.names: set[str] = set(extra_names)

    def is_target(self, ident: dict) -> bool:
        if not self.author_match:
            return True
        hay = f"{ident.get('displayName', '')} {ident.get('uniqueName', '')}".lower()
        return self.author_match in hay

    def role(self, ident: dict) -> str:
        key = ident.get("id") or ident.get("uniqueName") or ident.get("displayName") or "?"
        if key not in self.roles:
            self.names.add(ident.get("displayName", ""))
            self.roles[key] = f"colleague-{len(self.roles) + 1}"
        return self.roles[key]

    def text(self, s: str) -> str:
        s = MENTION.sub("[mention]", s or "")
        s = EMAIL.sub("[email]", s)
        s = URL.sub("[url]", s)
        s = GUID.sub("[id]", s)
        s = TOKENISH.sub("[token]", s)
        for name in sorted(self.names, key=len, reverse=True):
            for part in [name, *name.split()]:
                if len(part) >= 3:
                    s = re.sub(re.escape(part), "[name]", s, flags=re.IGNORECASE)
        return s.strip()


def rows_for_pr(base: str, pr: dict, author: str, redact=()):
    scrub = Scrubber(author, redact)
    threads = [t for t in get_threads(base, pr) if not t.get("isDeleted")]
    for t in threads:
        for c in t.get("comments", []):
            if c.get("author") and c.get("commentType") != "system":
                scrub.role(c["author"])
    for ident in [pr.get("createdBy") or {}, *(pr.get("reviewers") or [])]:
        if ident:
            scrub.role(ident)

    threads = [t for t in threads if any(c.get("commentType") != "system" for c in t.get("comments", []))]
    threads.sort(key=lambda t: t.get("publishedDate", ""))
    out = []
    for rank, t in enumerate(threads, start=1):
        comments = [c for c in t["comments"] if c.get("commentType") != "system" and not c.get("isDeleted")]
        if not comments or not scrub.is_target(comments[0].get("author") or {}):
            continue
        ctx = t.get("threadContext") or {}
        start = (ctx.get("rightFileStart") or ctx.get("leftFileStart") or {}).get("line", "")
        end = (ctx.get("rightFileEnd") or ctx.get("leftFileEnd") or {}).get("line", "")
        replies = [f"[{scrub.role(c['author'])}] {scrub.text(c.get('content', ''))}" for c in comments[1:]]
        out.append(
            {
                "repo": pr["repository"]["name"],
                "pr_id": pr["pullRequestId"],
                "pr_created": pr["creationDate"][:10],
                "pr_status": pr["status"],
                "thread_rank_in_pr": rank,
                "is_first_thread_in_pr": rank == 1,
                "thread_status": t.get("status", ""),
                "file": ctx.get("filePath", ""),
                "line_from": start,
                "line_to": end,
                "comment": scrub.text(comments[0].get("content", "")),
                "replies": " | ".join(replies),
                "reply_count": len(replies),
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", required=True, help="e.g. https://dev.azure.com/myorg")
    ap.add_argument("--project", required=True)
    ap.add_argument("--author", default="", help="substring of the reviewer's name or login; empty = everyone")
    ap.add_argument("--years", type=float, default=3)
    ap.add_argument("--repo", help="only this repository")
    ap.add_argument("--out", default=str(Path.home() / ".harness-feedback" / "mined"))
    ap.add_argument("--redact", default="", help="comma-separated names to blank out of the text (people not on the PR)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    redact = [n.strip() for n in a.redact.split(",") if n.strip()]
    base = f"{a.org.rstrip('/')}/{urllib.parse.quote(a.project)}"
    since = datetime.now(timezone.utc) - timedelta(days=round(365 * a.years))
    print(f"Listing pull requests since {since:%Y-%m-%d} ...", file=sys.stderr)
    prs = list_pull_requests(base, since, a.repo)

    print(f"Reading threads of {len(prs)} pull requests ...", file=sys.stderr)
    rows = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for i, part in enumerate(pool.map(lambda p: rows_for_pr(base, p, a.author, redact), prs), start=1):
            rows += part
            if i % 25 == 0:
                print(f"  {i}/{len(prs)}", file=sys.stderr)

    rows.sort(key=lambda r: (r["pr_created"], r["repo"], r["pr_id"], r["thread_rank_in_pr"]))
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"review-comments-{datetime.now():%Y%m%d}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["repo"])
        w.writeheader()
        w.writerows(rows)

    per_repo = defaultdict(int)
    for r in rows:
        per_repo[r["repo"]] += 1
    print(f"Wrote {len(rows)} threads from {len(prs)} pull requests to {out}", file=sys.stderr)
    for repo, n in sorted(per_repo.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {repo}", file=sys.stderr)


if __name__ == "__main__":
    main()
