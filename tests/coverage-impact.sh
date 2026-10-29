# Tests for harness/tools/testing/coverage-impact.py. Sourced by tests/run.sh: uses its expect helper and the
# $here, $h and $tmp variables. Fixtures are synthetic and built here; nothing runs a test suite or touches the network.
echo "== coverage-impact"
cvt="$h/tools/testing/coverage-impact.py"
cv="$tmp/covimpact"
cvr="$cv/repo"
rm -rf "$cv"
mkdir -p "$cvr/src/Shop.Core" "$cvr/src/Shop.Web" "$cvr/docs" "$cvr/tests/Shop.Core.UnitTests" "$cvr/outside" "$cv/outside"
for n in Pricing Discount Legacy Orphan Tax Dup; do
  printf 'l1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\nl9\nl10\n' >"$cvr/src/Shop.Core/$n.cs"
done
printf 'a\nb\nc\nd\ne\nf\n' >"$cvr/src/Shop.Web/checkout.ts"
echo hi >"$cvr/docs/readme.md"
echo t >"$cvr/tests/Shop.Core.UnitTests/PricingTests.cs"
echo x >"$cvr/outside/secret.cs"
echo s >"$cv/outside/secret.cs"
ln -s "$cv/outside/secret.cs" "$cvr/src/Shop.Core/Link.cs"
cvts=$(($(date +%s) + 5))
cvreal="$(cd "$cvr" && pwd -P)"

cat >"$cv/unit.xml" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<coverage line-rate="0.5" branch-rate="0" version="1.9" timestamp="$cvts">
  <sources><source>$cvr/src</source></sources>
  <packages><package name="Shop.Core"><classes>
    <class name="Shop.Core.Pricing" filename="Shop.Core/Pricing.cs"><methods/><lines>
      <line number="3" hits="4"/><line number="4" hits="4"/><line number="5" hits="2"/><line number="6" hits="0"/>
    </lines></class>
    <class name="Shop.Core.Pricing/Inner" filename="Shop.Core/Pricing.cs"><methods/><lines>
      <line number="3" hits="1"/><line number="7" hits="0"/>
    </lines></class>
    <class name="Shop.Core.Discount" filename="Shop.Core/Discount.cs"><methods/><lines>
      <line number="3" hits="0"/><line number="4" hits="0"/>
    </lines></class>
  </classes></package></packages>
</coverage>
EOF
cat >"$cv/integ.xml" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<coverage version="1.9" timestamp="$cvts">
  <sources><source>$cvr/src</source></sources>
  <packages><package name="Shop.Core"><classes>
    <class name="Shop.Core.Pricing" filename="Shop.Core/Pricing.cs"><methods/><lines>
      <line number="3" hits="1"/><line number="4" hits="0"/><line number="5" hits="0"/><line number="6" hits="0"/>
    </lines></class>
    <class name="Shop.Core.Discount" filename="Shop.Core/Discount.cs"><methods/><lines>
      <line number="3" hits="7"/><line number="4" hits="7"/>
    </lines></class>
    <class name="Shop.Core.Legacy" filename="Shop.Core/Legacy.cs"><methods/><lines>
      <line number="2" hits="0"/><line number="3" hits="0"/>
    </lines></class>
  </classes></package></packages>
</coverage>
EOF
cat >"$cv/e2e.info" <<EOF
TN:checkout journey places an order
SF:$cvr/src/Shop.Web/checkout.ts
DA:2,1
DA:3,1
DA:4,0
end_of_record
TN:checkout journey declines a card
SF:$cvreal/src/Shop.Web/checkout.ts
DA:2,1
DA:4,1
end_of_record
EOF
# Cobertura written on another machine with Windows paths and no sources; the repo folder name differs
cat >"$cv/win.xml" <<EOF
<?xml version="1.0"?>
<coverage version="1.9" timestamp="$cvts"><packages><package name="p"><classes>
  <class name="c" filename="C:\\agent\\_work\\1\\s\\src\\Shop.Core\\Pricing.cs"><lines>
    <line number="4" hits="1"/><line number="5" hits="1"/><line number="6" hits="1"/>
  </lines></class>
</classes></package></packages></coverage>
EOF
# Cobertura content under an .info name and lcov content under an .xml name: the format is detected by content
cp "$cv/integ.xml" "$cv/looks-like-lcov.info"
cp "$cv/e2e.info" "$cv/looks-like-xml.xml"

cat >"$cv/pr.diff" <<'EOF'
diff --git a/src/Shop.Core/Pricing.cs b/src/Shop.Core/Pricing.cs
index 111..222 100644
--- a/src/Shop.Core/Pricing.cs
+++ b/src/Shop.Core/Pricing.cs
@@ -4,2 +4,3 @@
-old
+new4
+new5
+new6
diff --git a/src/Shop.Core/Discount.cs b/src/Shop.Core/Discount.cs
--- a/src/Shop.Core/Discount.cs
+++ b/src/Shop.Core/Discount.cs
@@ -3,0 +4,2 @@
+x
+y
diff --git a/src/Shop.Core/Orphan.cs b/src/Shop.Core/Orphan.cs
--- a/src/Shop.Core/Orphan.cs
+++ b/src/Shop.Core/Orphan.cs
@@ -1 +1 @@
-a
+b
diff --git a/src/Shop.Core/Legacy.cs b/src/Shop.Core/Legacy.cs
--- a/src/Shop.Core/Legacy.cs
+++ b/src/Shop.Core/Legacy.cs
@@ -2,0 +3,2 @@
+m
+n
diff --git a/src/Shop.Web/checkout.ts b/src/Shop.Web/checkout.ts
--- a/src/Shop.Web/checkout.ts
+++ b/src/Shop.Web/checkout.ts
@@ -2,0 +3,2 @@
+q
+r
diff --git a/src/Shop.Core/Vat.cs b/src/Shop.Core/Tax.cs
similarity index 100%
rename from src/Shop.Core/Vat.cs
rename to src/Shop.Core/Tax.cs
diff --git a/src/Shop.Core/Gone.cs b/src/Shop.Core/Gone.cs
deleted file mode 100644
--- a/src/Shop.Core/Gone.cs
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
EOF
printf '%s\n' docs/readme.md tests/Shop.Core.UnitTests/PricingTests.cs >"$cv/extra.txt"
: >"$cv/empty.txt"

cov_json() { # cov_json <python expression over d and f(path)> <stdin file> <tool args...>
  local expr="$1" input="$2"
  shift 2
  python3 -I "$cvt" --json --root "$cvr" "$@" <"$input" >"$cv/out.json" 2>"$cv/err.txt" || { cat "$cv/err.txt"; return 1; }
  python3 -I -c '
import json, sys
d = json.load(open(sys.argv[1]))
f = lambda p: [x for x in d["files"] if x["path"] == p][0]
sys.exit(0 if eval(sys.argv[2]) else 1)' "$cv/out.json" "$expr" || { cat "$cv/out.json"; return 1; }
}
cov_has() { # cov_has <fixed text> <stdin file> <tool args...>: summary output contains the text
  local text="$1" input="$2"
  shift 2
  python3 -I "$cvt" --root "$cvr" "$@" <"$input" >"$cv/out.txt" 2>&1
  grep -qF -- "$text" "$cv/out.txt" || { cat "$cv/out.txt"; return 1; }
}
cov_run() { local input="$1"; shift; python3 -I "$cvt" --root "$cvr" "$@" <"$input"; }

U="--report unit=$cv/unit.xml"
I="--report integration=$cv/integ.xml"
E="--report e2e=$cv/e2e.info"
D="--diff $cv/pr.diff"

# the three questions, three layers, changed lines
expect 0 "summary on three layers runs" cov_run "$cv/empty.txt" $D $U $I $E
expect 0 "json: schema version, informational, limits and no threshold present" cov_json \
  'd["schema_version"]==1 and d["informational"] and len(d["limits"])>=3 and "threshold" not in json.dumps(d["summary"])' "$cv/empty.txt" $D $U $I $E
expect 0 "json: line-covered by unit, partial uncovered line named" cov_json \
  'f("src/Shop.Core/Pricing.cs")["status"]=="partial" and f("src/Shop.Core/Pricing.cs")["uncovered_ranges"]==[[6,6]] and f("src/Shop.Core/Pricing.cs")["covering_layers"]==["unit"]' "$cv/empty.txt" $D $U $I $E
expect 0 "json: a file covered only by an integration test is reported as such" cov_json \
  'f("src/Shop.Core/Discount.cs")["status"]=="covered" and f("src/Shop.Core/Discount.cs")["covering_layers"]==["integration"] and d["summary"]["files_covered_only_by"]["integration"]==["src/Shop.Core/Discount.cs"]' "$cv/empty.txt" $D $U $I $E
expect 0 "json: a file no test touches is reported as not in the report" cov_json \
  'f("src/Shop.Core/Orphan.cs")["status"]=="not_in_report" and "src/Shop.Core/Orphan.cs" in d["summary"]["uncovered_files"]' "$cv/empty.txt" $D $U $I $E
expect 0 "json: a file in the report with zero hits is uncovered" cov_json \
  'f("src/Shop.Core/Legacy.cs")["status"]=="uncovered" and f("src/Shop.Core/Legacy.cs")["covered_lines"]==0' "$cv/empty.txt" $D $U $I $E
expect 0 "json: lcov e2e coverage names the test cases and the layer" cov_json \
  'f("src/Shop.Web/checkout.ts")["covering_layers"]==["e2e"] and f("src/Shop.Web/checkout.ts")["covered_by"][0]["tests"]==["checkout journey declines a card","checkout journey places an order"]' "$cv/empty.txt" $D $U $I $E
expect 0 "json: layer distribution counts lines per layer" cov_json \
  'd["summary"]["covered_lines_by_layer"]=={"unit":2,"integration":1,"e2e":2} and d["summary"]["covered_only_by_layer"]=={"unit":2,"integration":1,"e2e":2}' "$cv/empty.txt" $D $U $I $E
expect 0 "json: duplicate class entries of one file merge (partial class, lambdas)" cov_json \
  'f("src/Shop.Core/Pricing.cs")["executable_lines"]==3' "$cv/empty.txt" $D $U
expect 0 "json: test file, non-code file and deleted file are not measured" cov_json \
  'f("docs/readme.md")["status"]=="not_code" and f("tests/Shop.Core.UnitTests/PricingTests.cs")["status"]=="test_file" and f("src/Shop.Core/Gone.cs")["status"]=="deleted"' "$cv/extra.txt" $D $U $I $E
expect 0 "json: the number is reported, never judged" cov_json \
  'abs(d["summary"]["line_coverage"]-d["summary"]["covered_lines"]/d["summary"]["executable_lines"])<0.001 and d["summary"]["executable_lines"]==7' "$cv/empty.txt" $D $U $I $E

# summary text carries the stance and the limits
# The default summary states both caveats in one line; --limits spells them out, so neither is buried.
expect 0 "summary says there is no threshold" cov_has "sets no threshold" "$cv/empty.txt" $D $U $I $E
expect 0 "summary says executed is not asserted" cov_has "Executed is not asserted" "$cv/empty.txt" $D $U $I $E
expect 0 "summary points at --limits" cov_has "--limits spells out" "$cv/empty.txt" $D $U $I $E
expect 0 "--limits gives the threshold reasoning in full" cov_has "a coverage threshold is a policy the harness has not set" "$cv/empty.txt" --limits $D $U $I $E
expect 0 "--limits gives the asserted caveat in full" cov_has "executed, not that behaviour was asserted" "$cv/empty.txt" --limits $D $U $I $E
expect 0 "default summary does not carry the full limit list" bash -c "! python3 -I '$cvt' --root '$cvr' $D $U $I $E <'$cv/empty.txt' 2>&1 | grep -qF 'Limit 1:'"
expect 0 "summary repeats the limit at the end" cov_has "Reading this: executed is not asserted" "$cv/empty.txt" $D $U $I $E
expect 0 "summary names the uncovered file" cov_has "src/Shop.Core/Orphan.cs: NOT IN ANY REPORT" "$cv/empty.txt" $D $U $I $E
expect 0 "summary flags integration-only coverage" cov_has "ONLY integration" "$cv/empty.txt" $D $U $I $E
expect 0 "summary flags e2e-only coverage against T.4" cov_has "T.4 asks for a layer 0 or 1 test" "$cv/empty.txt" $D $U $I $E
expect 0 "tool header documents the json schema and the tool contract" bash -c "grep -q 'schema_version 1' '$cvt' && grep -q 'Tool contract (Vegviser AI Tool Boundary)' '$cvt' && grep -q 'Classification:  Read' '$cvt'"

# stdin only: file granularity; name-status; renames
expect 0 "stdin paths without a diff report file-level granularity" cov_json \
  'd["summary"]["granularity"]=="file" and f("src/Shop.Core/Discount.cs")["granularity"]=="file"' <(echo src/Shop.Core/Discount.cs) $U $I
expect 0 "stdin name-status lines (D, R) are understood" cov_json \
  'f("src/Shop.Core/Gone.cs")["status"]=="deleted" and f("src/Shop.Core/Tax.cs")["old_path"]=="src/Shop.Core/Vat.cs"' <(printf 'D\tsrc/Shop.Core/Gone.cs\nR100\tsrc/Shop.Core/Vat.cs\tsrc/Shop.Core/Tax.cs\n') $U
expect 0 "a pure rename has no new lines to cover" cov_json \
  'f("src/Shop.Core/Tax.cs")["status"]=="no_executable_lines" and f("src/Shop.Core/Tax.cs")["old_path"]=="src/Shop.Core/Vat.cs"' "$cv/empty.txt" $D $U
cat >"$cv/rename.xml" <<EOF
<?xml version="1.0"?>
<coverage version="1.9" timestamp="$cvts"><sources><source>$cvr/src</source></sources><packages><package name="p"><classes>
  <class name="c" filename="Shop.Core/Vat.cs"><lines><line number="2" hits="1"/></lines></class>
</classes></package></packages></coverage>
EOF
cat >"$cv/rename-edit.diff" <<'EOF'
diff --git a/src/Shop.Core/Vat.cs b/src/Shop.Core/Tax.cs
similarity index 80%
rename from src/Shop.Core/Vat.cs
rename to src/Shop.Core/Tax.cs
--- a/src/Shop.Core/Vat.cs
+++ b/src/Shop.Core/Tax.cs
@@ -2 +2 @@
-a
+b
EOF
expect 0 "an edited rename the report only knows by its old name warns, makes no coverage claim" cov_json \
  'f("src/Shop.Core/Tax.cs")["status"]=="not_in_report" and d["stale"]["is_stale"] and d["stale"]["renamed_unknown_to_report"]==["src/Shop.Core/Tax.cs"] and any("old name" in n for n in f("src/Shop.Core/Tax.cs")["notes"])' "$cv/empty.txt" --diff "$cv/rename-edit.diff" --report unit="$cv/rename.xml"

# portability of report paths
expect 0 "Windows paths from another machine match by suffix" cov_json \
  'f("src/Shop.Core/Pricing.cs")["status"]=="covered" and f("src/Shop.Core/Pricing.cs")["report_match"][0]["match"]=="suffix"' "$cv/empty.txt" $D --report unit="$cv/win.xml"
expect 0 "format is detected by content: cobertura named .info" cov_json \
  'd["reports"][0]["format"]=="cobertura" and f("src/Shop.Core/Discount.cs")["status"]=="covered"' <(echo src/Shop.Core/Discount.cs) --report integration="$cv/looks-like-lcov.info"
expect 0 "format is detected by content: lcov named .xml" cov_json \
  'd["reports"][0]["format"]=="lcov" and f("src/Shop.Web/checkout.ts")["status"]=="covered"' <(echo src/Shop.Web/checkout.ts) --report e2e="$cv/looks-like-xml.xml"
expect 0 "an absolute report path matches whether the root is symlinked or resolved" cov_json \
  'f("src/Shop.Web/checkout.ts")["report_match"][0]["match"]=="exact"' <(echo src/Shop.Web/checkout.ts) $E
printf 'SF:/ci/a/src/Shop.Core/Dup.cs\nDA:2,1\nend_of_record\nSF:/ci/b/src/Shop.Core/Dup.cs\nDA:2,0\nend_of_record\n' >"$cv/dup.info"
expect 0 "two report paths that fit one changed file are ambiguous, not guessed" cov_json \
  'f("src/Shop.Core/Dup.cs")["status"]=="ambiguous" and f("src/Shop.Core/Dup.cs")["covered_lines"]==0' <(echo src/Shop.Core/Dup.cs) --report unit="$cv/dup.info"

# warnings
expect 0 "an unlabeled report with no layer signal warns that the layer is unknown" cov_json \
  'd["reports"][0]["layer"]=="unknown" and any("layer not inferable" in w for w in d["warnings"])' <(echo src/Shop.Core/Discount.cs) --report "$cv/integ.xml"
expect 0 "the layer is inferred from the report path convention" bash -c "
  mkdir -p '$cv/tests/Shop.IntegrationTests/TestResults/g1' && cp '$cv/integ.xml' '$cv/tests/Shop.IntegrationTests/TestResults/g1/coverage.cobertura.xml' &&
  cd '$cv' && echo src/Shop.Core/Discount.cs | python3 -I '$cvt' --root '$cvr' --json --report tests/Shop.IntegrationTests/TestResults/g1/coverage.cobertura.xml |
  python3 -I -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d[\"reports\"][0][\"layer\"]==\"integration\" and d[\"reports\"][0][\"layer_basis\"]==\"path\" else 1)'"
expect 0 "a single layer supplied warns that only-this-layer cannot be told apart" cov_json \
  'any("only one layer supplied" in w for w in d["warnings"])' "$cv/empty.txt" $D $U
sed "s/timestamp=\"[0-9]*\"/timestamp=\"1600000000\"/" "$cv/unit.xml" >"$cv/old.xml"
expect 0 "a report older than a changed file is called stale, loudly" cov_json \
  'd["stale"]["is_stale"] and d["warnings"][0].startswith("STALE REPORT") and any(x["path"]=="src/Shop.Core/Pricing.cs" for x in d["stale"]["files"])' "$cv/empty.txt" $D --report unit="$cv/old.xml"
expect 0 "stale warning is the first thing in the summary" bash -c "python3 -I '$cvt' --root '$cvr' --diff '$cv/pr.diff' --report unit='$cv/old.xml' </dev/null | grep -B1 -m1 'STALE REPORT' | grep -q 'Reports\\|unit:'"
cp "$cv/e2e.info" "$cv/old.info" && touch -t 202001010000 "$cv/old.info"
expect 0 "an lcov report has no timestamp: its file mtime decides staleness" cov_json \
  'd["stale"]["is_stale"] and d["reports"][0]["generated_at_source"]=="mtime"' <(echo src/Shop.Web/checkout.ts) --report e2e="$cv/old.info"
expect 0 "a fresh report is not stale" cov_json \
  'not d["stale"]["is_stale"] and d["stale"]["checked"]' "$cv/empty.txt" $D $U $I $E
expect 0 "a changed set that does not exist under the root warns" cov_json \
  'any("none of the changed paths exist" in w for w in d["warnings"])' <(echo src/Nothing/Here.cs) $U
expect 0 "no changed files is an answer, not an error" cov_json \
  'd["summary"]["changed_files"]==0 and d["summary"]["line_coverage"] is None' "$cv/empty.txt" $U
printf '<?xml version="1.0"?><coverage version="1.9"><packages/></coverage>\n' >"$cv/emptyreport.xml"
expect 0 "a report with no files warns, still answers" cov_json \
  'any("contains no files" in w for w in d["warnings"]) and f("src/Shop.Core/Pricing.cs")["status"]=="not_in_report"' <(echo src/Shop.Core/Pricing.cs) --report unit="$cv/emptyreport.xml"
cat >"$cv/zero.xml" <<EOF
<?xml version="1.0"?><coverage timestamp="$cvts"><sources><source>$cvr/src</source></sources><packages><package name="p"><classes>
<class name="c" filename="Shop.Core/Pricing.cs"><lines><line number="3" hits="0"/><line number="4" hits="0"/></lines></class>
</classes></package></packages></coverage>
EOF
expect 0 "zero coverage is reported, not failed (informational tool)" cov_json \
  'd["summary"]["line_coverage"]==0.0 and f("src/Shop.Core/Pricing.cs")["status"]=="uncovered"' <(echo src/Shop.Core/Pricing.cs) --report unit="$cv/zero.xml"

# usage errors and unparseable reports exit 2
expect 2 "no report argument" cov_run "$cv/empty.txt"
expect 2 "report path that does not exist" cov_run "$cv/empty.txt" --report "$cv/nope.xml"
echo 'not coverage at all' >"$cv/garbage.txt"
expect 2 "report that is not a coverage format" cov_run "$cv/empty.txt" --report "$cv/garbage.txt"
printf '<?xml version="1.0"?><coverage><packages><package>' >"$cv/truncated.xml"
expect 2 "truncated XML" cov_run "$cv/empty.txt" --report "$cv/truncated.xml"
printf '<?xml version="1.0"?><CoverageSession></CoverageSession>' >"$cv/opencover.xml"
expect 2 "XML that is not Cobertura" cov_run "$cv/empty.txt" --report "$cv/opencover.xml"
printf '<?xml version="1.0"?><!DOCTYPE coverage [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">]><coverage>&b;</coverage>' >"$cv/entity.xml"
expect 2 "XML with entity declarations is refused (untrusted input)" cov_run "$cv/empty.txt" --report "$cv/entity.xml"
expect 2 "--root that is not a directory" cov_run "$cv/empty.txt" --root "$cv/nope" $U
expect 2 "--diff that does not exist" cov_run "$cv/empty.txt" --diff "$cv/nope.diff" $U
expect 2 "unknown option" cov_run "$cv/empty.txt" --bogus $U
expect 2 "a directory as the report" cov_run "$cv/empty.txt" --report "$cv"

# untrusted input: paths never leave the root, escapes never reach the terminal
printf '%s\n' ../outside/secret.cs /etc/passwd /etc/hosts.cs 'src/../../x.cs' >"$cv/evil.txt"
expect 0 "paths outside the root are rejected, not read" cov_json \
  'all(x["status"]=="rejected" for x in d["files"]) and len(d["files"])==4 and not d["stale"]["files"] and d["summary"]["by_status"]=={"rejected":4}' "$cv/evil.txt" $U
expect 0 "rejected paths raise a warning" cov_json \
  'sum("changed path rejected" in w for w in d["warnings"])==4' "$cv/evil.txt" $U
expect 0 "an absolute path inside the root is accepted and made repo-relative" cov_json \
  'f("src/Shop.Core/Discount.cs")["status"]=="covered"' <(echo "$cvr/src/Shop.Core/Discount.cs") $I
expect 0 "a symlink that leaves the root is never statted" cov_json \
  'not any(x["path"]=="src/Shop.Core/Link.cs" for x in d["stale"]["files"]) and d["stale"]["checked"]==False' <(echo src/Shop.Core/Link.cs) --report unit="$cv/old.xml"
printf 'SF:../outside/secret.cs\nDA:2,5\nend_of_record\nSF:%s/../outside/secret.cs\nDA:2,5\nend_of_record\n' "$cvr" >"$cv/traversal.info"
expect 0 "a report path with '..' is ignored, so it cannot claim coverage of a file" cov_json \
  'f("outside/secret.cs")["status"]=="not_in_report" and d["reports"][0]["ignored_paths"]==2 and any("ignored" in w for w in d["warnings"])' <(echo outside/secret.cs) --report unit="$cv/traversal.info"
cat >"$cv/traversal.xml" <<EOF
<?xml version="1.0"?><coverage timestamp="$cvts"><sources><source>$cvr/src</source></sources><packages><package name="p"><classes>
<class name="c" filename="../../outside/secret.cs"><lines><line number="2" hits="9"/></lines></class>
</classes></package></packages></coverage>
EOF
expect 0 "a Cobertura filename with '..' is ignored" cov_json \
  'f("outside/secret.cs")["status"]=="not_in_report" and d["reports"][0]["ignored_paths"]==1' <(echo outside/secret.cs) --report unit="$cv/traversal.xml"
printf 'TN:\033[31mred\033]0;pwned\007\nSF:%s/src/Shop.Web/checkout.ts\nDA:3,1\nend_of_record\n' "$cvr" >"$cv/escape.info"
printf 'src/Shop.Web/checkout.ts\nsrc/\033[31mEvil.cs\n' >"$cv/escape.txt"
expect 0 "terminal escapes in test names and paths do not reach the summary" bash -c "
  python3 -I '$cvt' --root '$cvr' --report e2e='$cv/escape.info' < '$cv/escape.txt' | LC_ALL=C grep -q \$'\\033' && exit 1 || exit 0"
expect 0 "the escaped path is rejected" cov_json \
  'd["summary"]["by_status"].get("rejected")==1' "$cv/escape.txt" --report e2e="$cv/escape.info"
