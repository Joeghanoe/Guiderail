echo "== density"
# A synthetic bundle, so these assertions do not move when the real rules and playbooks do.
dens="$h/tools/harness/density.py"
db="$tmp/density"
mkdir -p "$db/harness/rules/cloud" "$db/harness/playbooks" "$db/harness/cases" "$db/harness/gates"
printf 'base instructions for every task\n' >"$db/AGENTS.base.md"
printf -- '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n* [Rules](rules/)\n' >"$db/harness/index.md"
printf '# Rules\n\n* [CLD.9](cld-9-shared-pipelines.md) - generated listing\n' >"$db/harness/rules/index.md"
shared="A change to a shared pipeline is written down as a command for a human to run (CLD.9)."
cat >"$db/harness/rules/cloud/cld-9-shared-pipelines.md" <<RULE
---
type: Rule
title: "CLD.9 Shared pipelines are changed by a human"
description: A shared pipeline change is proposed, never applied.
rule_id: CLD.9
applies_to: ["**/*.bicep"]
severity: blocker
---

# Rule

$shared

# Boundary

The reasoning here is what stops the reviewer applying this rule to a private pipeline.
RULE
cat >"$db/harness/playbooks/one.md" <<ONE
---
type: Playbook
title: One
description: Restates the rule inside a step.
---

# Steps

1. Read the run. $shared
ONE
cat >"$db/harness/playbooks/two.md" <<TWO
---
type: Playbook
title: Two
description: Restates the rule inside a protected section.
---

# Boundaries

$shared
TWO
cat >"$db/harness/playbooks/three.md" <<THREE
---
type: Playbook
title: Three
description: A section of narrative prose.
---

# Why

The reviewer experience improves when the reasoning behind a decision is reconstructible by the reader.
Teams that understand the trade-offs behind a boundary tend to respect it in their own work. A culture of
shared understanding grows from careful explanation rather than terse assertion.
THREE
cat >"$db/harness/cases/c-900-shared-pipeline.md" <<CASE
---
type: Case
title: "C-900 a shared pipeline change"
description: A case that quotes the rule.
case_id: C-900
rule: /rules/cloud/cld-9-shared-pipelines.md
verdict: violation
---

# Why (verdict)

$shared
CASE

for slot in x y; do
  cat >"$db/harness/gates/g-$slot.md" <<GATE
---
type: Gate
title: "Gate $slot"
description: One sentence around one parameter.
---

# Exception route

A description line \`$slot: n/a - <reason>\` of at least ten characters, seen by the reviewer.
GATE
done

den() { python3 -I "$dens" --root "$db/harness" "$@"; }
den duplicates --json >"$tmp/den-dup.json" 2>/dev/null
den candidates --json >"$tmp/den-cand.json" 2>/dev/null
den report --json >"$tmp/den-report.json" 2>/dev/null

expect 0 "density report runs over a bundle" den report
expect 0 "the repeated passage is found in every file that holds it" jq -e '
  [.duplicates[] | select(.text | test("written down as a command"))] | length == 1 and
  (.[0].files | sort == ["/cases/c-900-shared-pipeline.md", "/playbooks/one.md", "/playbooks/two.md",
   "/rules/cloud/cld-9-shared-pipelines.md"])' "$tmp/den-dup.json"
expect 0 "the rule that defines the ID is named as the definition site" jq -e '
  [.duplicates[] | select(.text | test("written down as a command"))][0]
  | .reason == "restatement" and .definition == "/rules/cloud/cld-9-shared-pipelines.md"' "$tmp/den-dup.json"
expect 0 "a repeat of one sentence around different parameters is a pattern, not a copy" jq -e '
  [.duplicates[] | select(.text | test("seen by the reviewer"))][0]
  | .reason == "pattern" and (.files | length == 2)' "$tmp/den-dup.json"
expect 0 "the cheapest and safest candidate ranks first" jq -e '
  .candidates[0] | .signal == "duplicate" and .risk == 1 and .file == "/playbooks/one.md"
  and .preserve == ["CLD.9"]' "$tmp/den-cand.json"
expect 0 "risk never decreases down the ranked list" jq -e '
  [.candidates[].risk] as $r | $r == ($r | sort)' "$tmp/den-cand.json"
expect 0 "narrative prose is a candidate, and ranks behind the duplicate" jq -e '
  ([.candidates[] | select(.signal == "narrative")] | length) > 0 and
  ([.candidates[] | select(.signal == "narrative")][0].risk > .candidates[0].risk)' "$tmp/den-cand.json"
expect 0 "every candidate carries a byte estimate and an action" jq -e '
  all(.candidates[]; .bytes > 0 and (.action | length) > 0)' "$tmp/den-cand.json"
expect 0 "a case is never suggested: it is the eval instrument" jq -e '
  ([.candidates[] | select(.file | startswith("/cases/"))] | length) == 0' "$tmp/den-cand.json"
expect 0 "the report says why a case is refused" jq -e '
  [.files[] | select(.file == "/cases/c-900-shared-pipeline.md")][0].refused | test("eval instrument")
  ' "$tmp/den-report.json"
expect 0 "a generated index is refused" jq -e '
  [.files[] | select(.file == "/rules/index.md")][0].refused | test("bundle.py index")' "$tmp/den-report.json"
expect 0 "a Boundaries section is never suggested" jq -e '
  ([.candidates[] | select(.section | test("Boundar"))] | length) == 0' "$tmp/den-cand.json"
expect 0 "the output states its own limits" bash -c '
  python3 -I "$1" --root "$2/harness" candidates 2>/dev/null | grep -q "never decides that a cut is safe"
  ' _ "$dens" "$db"
expect 0 "a narrow rule weighs less than a rule the sample paths all match" bash -c '
  printf "infra/main.bicep\nsrc/a.cs\n" >"$2/paths.txt";
  python3 -I "$1" --root "$2/harness" report --json --paths "$2/paths.txt" 2>/dev/null |
  jq -e "([.files[] | select(.file == \"/rules/cloud/cld-9-shared-pipelines.md\")][0].load_weight == 0.55)
         and ([.files[] | select(.file == \"/playbooks/one.md\")][0].load_weight == 0.1)"' _ "$dens" "$db"

mkdir -p "$tmp/density-empty/harness/rules"
expect 0 "an empty bundle produces no candidates" bash -c '
  python3 -I "$1" --root "$2/harness" candidates --json 2>/dev/null |
  jq -e ".candidates == [] and .identified_bytes == 0"' _ "$dens" "$tmp/density-empty"
mkdir -p "$tmp/density-bad/harness/rules"
printf -- '---\ntype: Rule\nrule_id: X\napplies_to: nope\n\n# Rule\n\n```\nunclosed fence\n' \
  >"$tmp/density-bad/harness/rules/broken.md"
: >"$tmp/density-bad/harness/rules/empty.md"
printf '%s\n' '| a | b |' '|---|---|' >"$tmp/density-bad/harness/rules/table-only.md"
expect 0 "malformed frontmatter, an unclosed fence and an empty file do not break it" bash -c '
  python3 -I "$1" --root "$2/harness" candidates --json 2>/dev/null | jq -e "has(\"candidates\")"
  ' _ "$dens" "$tmp/density-bad"
expect 2 "a bundle path that does not exist is reported, not guessed" python3 -I "$dens" --root "$tmp/density-nope" report
expect 2 "a shingle window too short to mean anything is refused" den duplicates --shingle 2
