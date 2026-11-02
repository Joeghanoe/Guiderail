#!/usr/bin/env node
// Compare two screenshot.mjs runs and print what a round of UI fixes changed (UI.1): which findings are fixed,
// which are new, which stayed. Needs Node 22+; no npm packages, no browser, no network. It reads two report.json
// files and nothing else.
//
// Tool contract (Vegviser AI Tool Boundary)
//   Classification:  Read. No state change; writes nothing but stdout and stderr.
//   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
//   Caller identity: the local user running the agent. It opens two local files and nothing else: no network,
//                    no browser, no credentials.
//   Inputs:          --before and --after, each a run folder or a report.json written by screenshot.mjs.
//                    Reports may describe personal data (SEC.2); the tool prints check names, WCAG ids, viewports and
//                    URLs, never the `detail` text of a finding.
//   Results:         a delta (fixed, new, reduced, increased, unchanged; totals per viewport) on stdout, or the same
//                    as JSON with --json; exit code below.
//   Side effects:    none.
//   Review trigger:  a change to the report.json shape in screenshot.mjs, or a new kind of finding whose `detail`
//                    carries a count in a format the parser below does not know.
//
// What the number is, and is not: findings are the built-in checks of screenshot.mjs plus axe-core when the repo has
// it installed. Together they cover part of WCAG 2.2 AA and say nothing about whether the screen is usable, fits its
// audience or shows only what the user needs (UI.2). A delta of zero is therefore not evidence that the UI got
// better, and a long list of fixed findings is not a design score. The number bounds the regression risk (did a
// fix trade one violation for another?); it does not grade the design. The reviewer still has to look (UI.1).
//
// Matching: a finding is the tuple (url, viewport, scheme, check). Array position and the `detail` text are not part
// of the key, because node counts and selectors inside `detail` change between runs. A node count is read from
// `detail` when it has one, as "7 nodes" or "3 elements" at the start (built-in checks) or "(7 nodes," (axe). Without
// one, the count is the number of findings of that check on that screen, and a single such finding is compared by
// presence only; the output says so. A drop in count is "reduced", a rise "increased"; neither counts as fixed or new.
// Runs must cover the same screens (url, viewport, scheme) and agree on whether axe ran, or the comparison would
// show missing coverage as fixes. Otherwise it stops; --allow-partial compares the overlap and says what it left out.
//
// Usage: node compare-ui.mjs --before <run-dir|report.json> --after <run-dir|report.json>
//          [--json] [--baseline-name <label>] [--after-name <label>] [--allow-partial]
// Output: a delta table on stdout: summary, totals per viewport, then new, increased, reduced, fixed and unchanged
//         findings, each with the viewports where it occurs. With --json the same delta as one JSON object.
// Exit:   0 no regression (findings may be fixed, reduced or unchanged), 1 usage or read error (including
//         runs that cover different screens), 2 a regression: at least one new finding, or one whose node
//         count rose. More violations of a check the baseline already had is a regression like any other.
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const CEILING =
  "Scope: built-in checks and axe-core only, which cover part of WCAG 2.2 AA and nothing about usability or fit for the audience. " +
  "A delta of zero is not evidence the UI improved; this bounds the regression risk and does not score the design. Look at the screenshots (UI.1, UI.2).";

function fail(message) {
  console.error(`compare-ui.mjs: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const options = { before: "", after: "", "baseline-name": "before", "after-name": "after" };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--json") options.json = true;
    else if (arg === "--allow-partial") options.allowPartial = true;
    else if (["--before", "--after", "--baseline-name", "--after-name"].includes(arg)) {
      const value = argv[++i];
      if (!value || value.startsWith("--")) fail(`${arg} needs a value`);
      options[arg.slice(2)] = value;
    } else fail(`unknown option ${arg}`);
  }
  if (!options.before || !options.after) fail("both --before and --after are required");
  return options;
}

function readReport(input, label) {
  let path = input;
  if (!existsSync(path)) fail(`--${label}: ${input} does not exist`);
  if (statSync(path).isDirectory()) {
    path = join(path, "report.json");
    if (!existsSync(path)) fail(`--${label}: ${input} has no report.json (is it a screenshot.mjs run folder?)`);
  }
  let report;
  try {
    report = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    fail(`--${label}: ${path} is not readable JSON (${error.message})`);
  }
  if (!report || typeof report !== "object" || !Array.isArray(report.shots)) fail(`--${label}: ${path} is not a screenshot.mjs report (no "shots" array)`);
  report.shots.forEach((shot, index) => {
    const where = `--${label}: ${path}, shots[${index}]`;
    if (!shot || typeof shot !== "object") fail(`${where} is not an object`);
    for (const key of ["url", "viewport", "scheme"]) if (typeof shot[key] !== "string" || !shot[key]) fail(`${where} has no "${key}"`);
    if (!Array.isArray(shot.findings)) fail(`${where} has no "findings" array`);
    shot.findings.forEach((f, n) => {
      if (!f || typeof f !== "object" || typeof f.check !== "string" || !f.check) fail(`${where}, findings[${n}] has no "check"`);
    });
  });
  return { path, axeRan: report.axe === "run", axe: typeof report.axe === "string" ? report.axe : "not recorded", shots: report.shots };
}

// A count read from a finding's detail text, or null when the detail carries none.
function nodeCount(detail) {
  if (typeof detail !== "string") return null;
  const match = /^\s*(\d+)\s+(?:nodes?|elements?|instances?)\b/i.exec(detail) ?? /\((\d+)\s+nodes?\b/i.exec(detail);
  return match ? Number(match[1]) : null;
}

const screenOf = (shot) => [shot.url, shot.viewport, shot.scheme].join("\u0000");
const keyOf = (shot, check) => [shot.url, shot.viewport, shot.scheme, check].join("\u0000");

// Group a run's findings by tuple. Several findings of one check on one screen (one per element) become one entry.
function index(report, skipAxe) {
  const screens = new Set();
  const findings = new Map();
  for (const shot of report.shots) {
    screens.add(screenOf(shot));
    for (const f of shot.findings) {
      if (skipAxe && f.check.startsWith("axe:")) continue;
      const key = keyOf(shot, f.check);
      const entry = findings.get(key) ?? { url: shot.url, viewport: shot.viewport, scheme: shot.scheme, check: f.check, wcag: f.wcag ?? "", entries: 0, counts: [] };
      entry.entries++;
      entry.counts.push(nodeCount(f.detail));
      findings.set(key, entry);
    }
  }
  for (const entry of findings.values()) {
    const parsed = entry.counts.every((c) => c !== null);
    entry.basis = parsed ? "nodes" : "findings";
    entry.count = parsed ? entry.counts.reduce((a, b) => a + b, 0) : entry.entries;
  }
  return { screens, findings };
}

const describeScreen = (screen) => {
  const [url, viewport, scheme] = screen.split("\u0000");
  return `${url} @ ${viewport}${scheme === "dark" ? " dark" : ""}`;
};

function compare(before, after, options) {
  const skipAxe = before.axeRan !== after.axeRan;
  const a = index(before, skipAxe);
  const b = index(after, skipAxe);
  const onlyBefore = [...a.screens].filter((s) => !b.screens.has(s));
  const onlyAfter = [...b.screens].filter((s) => !a.screens.has(s));
  const problems = [];
  if (onlyBefore.length || onlyAfter.length) {
    problems.push(
      `the runs cover different screens: ${onlyBefore.length} only in ${options["baseline-name"]}, ${onlyAfter.length} only in ${options["after-name"]}. ` +
        `A screen missing from one run would show as fixed or new without being either. Capture again with the same --url, --viewports and --scheme.`,
    );
  }
  if (skipAxe) {
    problems.push(
      `axe-core ran in ${before.axeRan ? options["baseline-name"] : options["after-name"]} but not in ${before.axeRan ? options["after-name"] : options["baseline-name"]} ` +
        `(${before.axeRan ? after.axe : before.axe}). Install axe-core in the repo and capture both runs again.`,
    );
  }
  if (problems.length && !options.allowPartial) {
    fail(`${problems.join(" ")} Pass --allow-partial to compare only what both runs share.`);
  }

  const shared = new Set([...a.screens].filter((s) => b.screens.has(s)));
  const rows = [];
  for (const [key, was] of a.findings) {
    if (!shared.has(screenOf(was))) continue;
    const now = b.findings.get(key);
    if (!now) rows.push({ ...was, status: "fixed", before: was.count, after: 0, basis: was.basis });
    else if (was.basis !== now.basis) rows.push({ ...now, status: "unchanged", before: was.count, after: now.count, basis: "not comparable", note: "counts not comparable between the runs" });
    else if (now.count < was.count) rows.push({ ...now, status: "reduced", before: was.count, after: now.count });
    else if (now.count > was.count) rows.push({ ...now, status: "increased", before: was.count, after: now.count });
    else rows.push({ ...now, status: "unchanged", before: was.count, after: now.count });
  }
  for (const [key, now] of b.findings) {
    if (shared.has(screenOf(now)) && !a.findings.has(key)) rows.push({ ...now, status: "new", before: 0, after: now.count });
  }
  for (const row of rows) {
    if (row.status === "unchanged" && row.basis === "findings" && row.before === 1 && row.after === 1) row.note = "no node count in detail; compared by presence only";
  }

  const viewports = [...new Set([...shared].map((s) => s.split("\u0000")[1]))].sort((x, y) => parseInt(x, 10) - parseInt(y, 10));
  const perViewport = viewports.map((viewport) => {
    const inViewport = rows.filter((r) => r.viewport === viewport);
    const count = (...statuses) => inViewport.filter((r) => statuses.includes(r.status)).length;
    return {
      viewport,
      before: count("fixed", "reduced", "increased", "unchanged"),
      after: count("new", "reduced", "increased", "unchanged"),
      fixed: count("fixed"),
      new: count("new"),
      reduced: count("reduced"),
      increased: count("increased"),
    };
  });
  const summary = Object.fromEntries(["new", "increased", "reduced", "fixed", "unchanged"].map((s) => [s, rows.filter((r) => r.status === s).length]));
  return {
    before: { name: options["baseline-name"], report: before.path, axe: before.axe },
    after: { name: options["after-name"], report: after.path, axe: after.axe },
    partial: problems.length > 0 ? { compared: shared.size, onlyBefore: onlyBefore.map(describeScreen), onlyAfter: onlyAfter.map(describeScreen), axeExcluded: skipAxe } : null,
    screensCompared: shared.size,
    summary,
    perViewport,
    findings: rows.map(({ url, viewport, scheme, check, wcag, status, before: n, after: m, basis, note }) => ({ url, viewport, scheme, check, wcag, status, before: n, after: m, countBasis: basis, ...(note ? { note } : {}) })),
    scope: CEILING,
  };
}

// One line per (status, url, check), with the viewports where it occurs, as screenshot.mjs does for its own summary.
function printTable(delta) {
  const { before, after, summary, perViewport } = delta;
  const nameWidth = Math.max(before.name.length, after.name.length, 6);
  console.log(`${before.name}: ${before.report}  (axe-core: ${before.axe})`);
  console.log(`${after.name}: ${after.report}  (axe-core: ${after.axe})`);
  console.log(`compared ${delta.screensCompared} screen(s) (url x viewport x scheme); findings matched on (url, viewport, scheme, check)`);
  if (delta.partial) {
    console.log(`PARTIAL (--allow-partial): left out ${delta.partial.onlyBefore.length + delta.partial.onlyAfter.length} screen(s)${delta.partial.axeExcluded ? " and every axe:* check" : ""}:`);
    for (const s of delta.partial.onlyBefore) console.log(`  only in ${before.name}: ${s}`);
    for (const s of delta.partial.onlyAfter) console.log(`  only in ${after.name}: ${s}`);
  }
  console.log(`\nnew ${summary.new}, increased ${summary.increased}, reduced ${summary.reduced}, fixed ${summary.fixed}, unchanged ${summary.unchanged}`);

  console.log("\nFindings per viewport:");
  const header = ["viewport".padEnd(10), before.name.padStart(nameWidth), after.name.padStart(nameWidth), "fixed".padStart(6), "new".padStart(5), "reduced".padStart(8), "increased".padStart(10)];
  console.log(`  ${header.join("  ")}`);
  for (const v of perViewport) {
    const cells = [v.viewport.padEnd(10), String(v.before).padStart(nameWidth), String(v.after).padStart(nameWidth), String(v.fixed).padStart(6), String(v.new).padStart(5), String(v.reduced).padStart(8), String(v.increased).padStart(10)];
    console.log(`  ${cells.join("  ")}${v.new > 0 ? "  <- worse" : ""}`);
  }

  const sections = [
    ["new", "NEW (absent in the baseline, present now: a regression)"],
    ["increased", "INCREASED (same finding, more nodes than before)"],
    ["reduced", "REDUCED (same finding, fewer nodes; not fixed)"],
    ["fixed", "FIXED (present in the baseline, gone now)"],
    ["unchanged", "UNCHANGED"],
  ];
  for (const [status, title] of sections) {
    const rows = delta.findings.filter((r) => r.status === status);
    if (rows.length === 0) continue;
    console.log(`\n${title}:`);
    const groups = new Map();
    for (const r of rows) {
      const key = `${r.url}\u0000${r.check}\u0000${r.wcag}`;
      const place = `${r.viewport}${r.scheme === "dark" ? " dark" : ""}`;
      const unit = r.countBasis === "nodes" ? "nodes" : "findings";
      const text = status === "reduced" || status === "increased" ? `${place} (${r.before} -> ${r.after} ${unit})` : place;
      groups.set(key, [...(groups.get(key) ?? []), text]);
    }
    for (const [key, places] of groups) {
      const [url, check, wcag] = key.split("\u0000");
      console.log(`  [${check}] WCAG ${wcag || "-"}  ${url}  @ ${places.join(", ")}`);
    }
  }
  const presenceOnly = delta.findings.filter((r) => r.note && r.note.startsWith("no node count")).length;
  const incomparable = delta.findings.filter((r) => r.note && r.note.startsWith("counts not comparable")).length;
  if (presenceOnly) console.log(`\n${presenceOnly} unchanged finding(s) have no node count in their detail and were compared by presence only; a smaller count there would not show.`);
  if (incomparable) console.log(`${incomparable} unchanged finding(s) had a node count in one run and not the other; compared by presence only.`);

  console.log(`\n${delta.scope}`);
  if (summary.new > 0 || summary.increased > 0) {
    const parts = [];
    if (summary.new > 0) parts.push(`${summary.new} new finding(s) the baseline did not have`);
    if (summary.increased > 0) parts.push(`${summary.increased} finding(s) with more nodes than before`);
    console.log(`result: ${parts.join(" and ")}, exit 2. This is a regression; look at it before anything else.`);
  } else console.log("result: no regression, exit 0.");
}

function run() {
  const options = parseArgs(process.argv.slice(2));
  const delta = compare(readReport(options.before, "before"), readReport(options.after, "after"), options);
  if (options.json) console.log(JSON.stringify(delta, null, 2));
  else printTable(delta);
  process.exit(delta.summary.new > 0 || delta.summary.increased > 0 ? 2 : 0);
}

try {
  run();
} catch (error) {
  fail(error.message);
}
