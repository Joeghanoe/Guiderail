// Tests for screenshot.mjs --auth-state. Run by tests/run.sh; the browser test is skipped when no Chrome, Edge or Chromium is installed.
import assert from "node:assert/strict";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import { cookieParams, describeAuthState, parseAuthState, seedScript } from "../harness/tools/frontend/auth-state.mjs";
import { buildMsalSessionStorage, decodeClaims, fakeIdToken } from "../harness/tools/frontend/auth-examples/msal-client-credentials.mjs";

const tool = fileURLToPath(new URL("../harness/tools/frontend/screenshot.mjs", import.meta.url));
const SECRET = "sentinel-token-value-123";

test("a valid state is normalised and clears storage by default", () => {
  const state = parseAuthState(JSON.stringify({ origin: "http://localhost:5173/x", sessionStorage: { k: SECRET }, cookies: [{ name: "c", value: "v" }] }));
  assert.equal(state.origin, "http://localhost:5173");
  assert.equal(state.clear, true);
  assert.equal(state.cookies[0].path, "/");
});

test("bad files are refused and the message never contains a value", () => {
  const bad = [
    "not json",
    "[]",
    JSON.stringify({ sessionStorage: { k: 5 }, extra: SECRET }),
    JSON.stringify({ sessionStorage: { k: SECRET }, unknown: SECRET }),
    JSON.stringify({ origin: "ftp://x", sessionStorage: { k: SECRET } }),
    JSON.stringify({ cookies: [{ name: "c", value: SECRET, sameSite: "Sometimes" }] }),
    JSON.stringify({ cookies: [{ name: "c", value: SECRET, extra: 1 }] }),
    JSON.stringify({ localStorage: { k: "x".repeat(70000) } }),
    JSON.stringify({}),
  ];
  for (const text of bad) {
    assert.throws(() => parseAuthState(text), (error) => /^auth state: /.test(error.message) && !error.message.includes(SECRET));
  }
});

function pageFor(origin, { top = true, existing = {} } = {}) {
  const store = (initial) => {
    const data = { ...initial };
    return { data, clear: () => Object.keys(data).forEach((k) => delete data[k]), setItem: (k, v) => (data[k] = v) };
  };
  const win = { sessionStorage: store(existing), localStorage: store({}), location: { origin } };
  win.window = win;
  win.top = top ? win : {};
  return win;
}

test("the seed script clears, then seeds, in the top frame of the named origin only", () => {
  const state = parseAuthState(JSON.stringify({ sessionStorage: { token: SECRET }, localStorage: { who: "e2e" } }));
  const script = seedScript(state, "http://localhost:5173");

  const here = pageFor("http://localhost:5173", { existing: { stale: "old" } });
  vm.runInNewContext(script, here);
  assert.deepEqual(here.sessionStorage.data, { token: SECRET });
  assert.deepEqual(here.localStorage.data, { who: "e2e" });

  const elsewhere = pageFor("https://evil.example", { existing: { keep: "1" } });
  vm.runInNewContext(script, elsewhere);
  assert.deepEqual(elsewhere.sessionStorage.data, { keep: "1" });

  const frame = pageFor("http://localhost:5173", { top: false });
  vm.runInNewContext(script, frame);
  assert.deepEqual(frame.sessionStorage.data, {});
});

test("clear:false keeps what the page already had", () => {
  const state = parseAuthState(JSON.stringify({ clear: false, sessionStorage: { token: "t" } }));
  const page = pageFor("http://localhost:1", { existing: { keep: "1" } });
  vm.runInNewContext(seedScript(state, "http://localhost:1"), page);
  assert.deepEqual(page.sessionStorage.data, { keep: "1", token: "t" });
});

test("the report description carries counts only", () => {
  const state = parseAuthState(JSON.stringify({ sessionStorage: { token: SECRET }, cookies: [{ name: "c", value: SECRET }] }));
  const text = JSON.stringify(describeAuthState(state, "http://localhost:1"));
  assert.ok(!text.includes(SECRET));
  assert.deepEqual(cookieParams(state, "http://localhost:1")[0].url, "http://localhost:1");
});

test("the MSAL example builds the cache layout the Aquarium Cypress login uses", () => {
  const claims = { oid: "OID", tid: "TID", roles: ["Operator"] };
  const accessToken = `${Buffer.from("{}").toString("base64url")}.${Buffer.from(JSON.stringify(claims)).toString("base64url")}.sig`;
  const entries = buildMsalSessionStorage({ accessToken, expiresIn: 3600, clientId: "CLIENT", now: 1_000_000 });
  const keys = Object.keys(entries);
  assert.ok(keys.includes("msal.2.account.keys"));
  assert.ok(keys.includes("msal.2.token.keys.CLIENT"));
  assert.ok(keys.includes("msal.CLIENT.active-account-filters"));
  const separated = keys.filter((k) => k.includes("|"));
  assert.equal(separated.length, 3); // account, id token, access token
  assert.ok(separated.every((k) => k === k.toLowerCase()));
  const idToken = Object.values(entries).map((v) => JSON.parse(v)).find((v) => v.credentialType === "IdToken");
  assert.deepEqual(decodeClaims(idToken.secret).roles, ["Operator"]);
  const access = Object.values(entries).map((v) => JSON.parse(v)).find((v) => v.credentialType === "AccessToken");
  assert.equal(access.secret, accessToken);
  assert.equal(access.expiresOn, String(1000 + 3600));
  assert.throws(() => buildMsalSessionStorage({ accessToken: fakeIdToken({}), expiresIn: 1, clientId: "C" }), /oid or tid/);
});

test("a state file inside a git repository that does not ignore it is refused", () => {
  const repo = mkdtempSync(join(tmpdir(), "auth-repo-"));
  try {
    execFileSync("git", ["init", "-q"], { cwd: repo });
    const file = join(repo, "state.json");
    writeFileSync(file, JSON.stringify({ sessionStorage: { token: SECRET } }));
    const result = spawnSync("node", [tool, "--url", "http://localhost:1/", "--auth-state", file], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /not ignored/);
    assert.ok(!result.stderr.includes(SECRET));
  } finally {
    rmSync(repo, { recursive: true, force: true });
  }
});

test("a missing state file is refused", () => {
  const result = spawnSync("node", [tool, "--url", "http://localhost:1/", "--auth-state", join(tmpdir(), "nope-state.json")], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /not found/);
});

const BROWSERS = [
  process.env.HARNESS_BROWSER,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/microsoft-edge",
];
const hasBrowser = BROWSERS.some((b) => b && existsSync(b));

test("a page behind a login is captured logged in, and the secret never reaches the report", { skip: hasBrowser ? false : "no Chrome, Edge or Chromium installed" }, async () => {
  // The page shows a login prompt unless sessionStorage holds the token; only the logged-in page has an <img> without alt text.
  const html = `<!doctype html><html lang="nl"><head><title>t</title><meta name="viewport" content="width=device-width"></head><body><main><h1>x</h1><div id="a"></div></main>
<script>document.getElementById('a').innerHTML = sessionStorage.getItem('token') === '${SECRET}' ? '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">' : '<p>Log in</p>';</script></body></html>`;
  const server = createServer((_, res) => res.setHeader("content-type", "text/html").end(html));
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const url = `http://127.0.0.1:${server.address().port}/`;
  const dir = mkdtempSync(join(tmpdir(), "auth-shot-"));
  try {
    const stateFile = join(dir, "state.json");
    writeFileSync(stateFile, JSON.stringify({ sessionStorage: { token: SECRET } }));
    // async: this process serves the page, so it must not block while the tool runs
    const run = async (name, extra) => {
      const out = join(dir, name);
      mkdirSync(out);
      const child = spawn("node", [tool, "--url", url, "--viewports", "390x844", "--wait", "300", "--out", out, ...extra], { stdio: ["ignore", "pipe", "pipe"] });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (c) => (stdout += c));
      child.stderr.on("data", (c) => (stderr += c));
      const status = await new Promise((resolve) => child.on("exit", resolve));
      assert.equal(status, 0, stderr);
      assert.ok(!stdout.includes(SECRET));
      return { report: readFileSync(join(out, "report.json"), "utf8"), stdout };
    };
    const loggedOut = await run("out", []);
    const loggedIn = await run("in", ["--auth-state", stateFile]);
    assert.ok(!loggedOut.report.includes("img-alt"));
    assert.ok(loggedIn.report.includes("img-alt"), "the seeded page did not render logged in");
    assert.ok(!loggedIn.report.includes(SECRET));
    assert.match(loggedIn.stdout, /auth state: applied to/);
  } finally {
    server.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
