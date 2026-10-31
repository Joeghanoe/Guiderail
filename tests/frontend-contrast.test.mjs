// Tests for tools/frontend/contrast.mjs. Run by tests/run.sh.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { check, parseColor, ratio, readTokens } from "../harness/tools/frontend/contrast.mjs";

const tool = fileURLToPath(new URL("../harness/tools/frontend/contrast.mjs", import.meta.url));
const CSS = `:root { --color-orange: #d9661f; --color-green: #5aab46; --color-green-dark: #3f8a2e; --color-green-darker: #357a27;
  --color-text: #555555; --color-bg: #ffffff; }
@media (prefers-color-scheme: dark) { :root { --color-bg: #111111; } }`;

test("black on white is 21:1 and the ratio is symmetric", () => {
  assert.equal(Math.round(ratio([0, 0, 0], [255, 255, 255])), 21);
  assert.equal(ratio([10, 20, 30], [200, 210, 220]), ratio([200, 210, 220], [10, 20, 30]));
});

test("short and long hex colours parse, other values do not", () => {
  assert.deepEqual(parseColor("#fff"), [255, 255, 255]);
  assert.deepEqual(parseColor("#D9661F"), [217, 102, 31]);
  assert.equal(parseColor("rgb(1,2,3)"), null);
});

test("the first declaration of a token wins, so a dark-scheme override is not the token", () => {
  assert.equal(readTokens(CSS).get("--color-bg"), "#ffffff");
});

test("the style-guide pairs that failed AA fail, and the darker ones pass", () => {
  const tokens = readTokens(CSS);
  const results = check(
    [
      { fg: "color-orange", bg: "color-bg", large: false }, // the guide says about 3.9:1; it is 3.58:1
      { fg: "#ffffff", bg: "color-green-dark", large: false }, // the guide's "accessible" button green: 4.30:1
      { fg: "#ffffff", bg: "color-green-darker", large: false },
      { fg: "color-text", bg: "color-bg", large: false },
      { fg: "color-orange", bg: "color-bg", large: true },
    ],
    tokens,
  );
  assert.deepEqual(results.map((r) => r.ok), [false, false, true, true, true]);
  assert.ok(results[0].got > 3.5 && results[0].got < 3.7);
  assert.ok(results[1].got > 4.2 && results[1].got < 4.4);
});

function run(args) {
  const dir = mkdtempSync(join(tmpdir(), "contrast-"));
  try {
    writeFileSync(join(dir, "tokens.css"), CSS);
    return spawnSync("node", [tool, "--css", join(dir, "tokens.css"), ...args], { encoding: "utf8" });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("the command exits 1 on a failing pair and says which", () => {
  const result = run(["--pair", "color-orange/color-bg"]);
  assert.equal(result.status, 1);
  assert.match(result.stdout, /FAIL\s+3\.5\d:1 \(needs 4\.5:1\)\s+--color-orange #d9661f on --color-bg #ffffff/);
});

test("the command exits 0 when every pair passes", () => {
  assert.equal(run(["--pair", "color-text/color-bg", "--large", "color-orange/color-bg"]).status, 0);
});

test("an unknown token or a missing pair is an error, not a pass", () => {
  assert.equal(run(["--pair", "color-nope/color-bg"]).status, 1);
  assert.equal(run([]).status, 1);
  assert.equal(run(["--pair", "justone"]).status, 1);
});
