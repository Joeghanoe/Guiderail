#!/usr/bin/env node
// Screenshot a running page at several viewports and run the automated UI checks (UI.1).
// Needs Node 22+ and an installed Chrome, Edge or Chromium; no npm packages. The page must already be running:
// this tool never starts, builds or deploys the app, and only opens http(s) URLs on localhost unless --allow-remote.
//
// Usage: node screenshot.mjs --url <url> [--url <url> ...] [--out <dir>] [--name <prefix>]
//          [--viewports 320x640,390x844,768x1024,1280x800] [--scheme light|dark|both] [--wait <ms>] [--full-page]
//          [--scale 1] [--keep-days 7] [--max-mb 200] [--allow-remote]
// Output: <out>/<name>-<w>x<h>[-dark].png and <out>/report.json; a one-line-per-finding summary on stdout.
//         Without --out the run goes to ~/.harness-screenshots/<repo>/<timestamp>/, outside every repo, and runs older
//         than --keep-days, or beyond --max-mb in total (oldest first), are deleted before the capture. Only run
//         folders that hold this tool's report.json are ever deleted; an explicit --out is never pruned.
// Exit:   0 captured (findings are information, the reviewer decides), 1 usage or capture error.
import { execFileSync, spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir, tmpdir } from "node:os";
import { basename, join } from "node:path";

const SHOTS_ROOT = join(homedir(), ".harness-screenshots");
const DEFAULT_VIEWPORTS = "320x640,390x844,768x1024,1280x800";
const BROWSERS = [
  process.env.HARNESS_BROWSER,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/microsoft-edge",
  String.raw`C:\Program Files\Google\Chrome\Application\chrome.exe`,
  String.raw`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`,
];

function fail(message) {
  console.error(`screenshot.mjs: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const options = { urls: [], out: "", name: "", viewports: DEFAULT_VIEWPORTS, scheme: "light", wait: 600, scale: 1, "keep-days": 7, "max-mb": 200 };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--full-page") options.fullPage = true;
    else if (arg === "--allow-remote") options.allowRemote = true;
    else if (arg === "--url") options.urls.push(argv[++i]);
    else if (["--out", "--name", "--viewports", "--scheme", "--wait", "--scale", "--keep-days", "--max-mb"].includes(arg)) options[arg.slice(2)] = argv[++i];
    else fail(`unknown option ${arg}`);
  }
  for (const key of ["wait", "scale", "keep-days", "max-mb"]) {
    options[key] = Number(options[key]);
    if (!(options[key] >= 0)) fail(`--${key} must be a number`);
  }
  if (options.urls.length === 0 || options.urls.some((u) => !u)) fail("at least one --url is required");
  if (!["light", "dark", "both"].includes(options.scheme)) fail("--scheme is light, dark or both");
  return options;
}

function checkUrl(raw, allowRemote) {
  let url;
  try {
    url = new URL(raw);
  } catch {
    fail(`not a URL: ${raw}`);
  }
  if (!["http:", "https:"].includes(url.protocol)) fail(`only http(s) URLs are opened: ${raw}`);
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (!local && !allowRemote) fail(`${url.hostname} is not localhost; pass --allow-remote if the user asked for it`);
  return url.href;
}

function parseViewports(text) {
  return text.split(",").map((v) => {
    const match = /^(\d+)x(\d+)$/.exec(v.trim());
    if (!match) fail(`bad viewport ${v}, expected WIDTHxHEIGHT`);
    const [width, height] = [Number(match[1]), Number(match[2])];
    return { width, height, mobile: width < 768 };
  });
}

function repoName() {
  try {
    const top = execFileSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    return basename(top);
  } catch {
    return basename(process.cwd());
  }
}

function folderBytes(dir) {
  return readdirSync(dir, { withFileTypes: true }).reduce((sum, entry) => {
    const path = join(dir, entry.name);
    return sum + (entry.isDirectory() ? folderBytes(path) : statSync(path).size);
  }, 0);
}

// Deletes old run folders under the shots root: too old first, then oldest-first until the total fits max-mb.
// A folder is a run only when it sits two levels down (<repo>/<run>) and holds our report.json.
function pruneRuns(keepDays, maxMb) {
  if (!existsSync(SHOTS_ROOT)) return { removed: 0, freedMb: 0 };
  const runs = [];
  for (const repo of readdirSync(SHOTS_ROOT, { withFileTypes: true }).filter((e) => e.isDirectory())) {
    for (const run of readdirSync(join(SHOTS_ROOT, repo.name), { withFileTypes: true }).filter((e) => e.isDirectory())) {
      const dir = join(SHOTS_ROOT, repo.name, run.name);
      if (existsSync(join(dir, "report.json"))) runs.push({ dir, time: statSync(join(dir, "report.json")).mtimeMs, bytes: folderBytes(dir) });
    }
  }
  runs.sort((a, b) => a.time - b.time);
  const cutoff = Date.now() - keepDays * 86400000;
  let total = runs.reduce((sum, r) => sum + r.bytes, 0);
  let removed = 0;
  let freed = 0;
  for (const run of runs) {
    if (run.time >= cutoff && total <= maxMb * 1048576) break;
    rmSync(run.dir, { recursive: true, force: true });
    total -= run.bytes;
    freed += run.bytes;
    removed++;
  }
  return { removed, freedMb: Math.round(freed / 1048576) };
}

function findBrowser() {
  const found = BROWSERS.find((path) => path && existsSync(path));
  if (!found) fail("no Chrome, Edge or Chromium found; install one or set HARNESS_BROWSER to its executable");
  return found;
}

// axe-core is used when the repo has it installed; without it only the built-in checks run, and the report says so.
function loadAxe() {
  try {
    const path = createRequire(join(process.cwd(), "noop.js")).resolve("axe-core/axe.min.js");
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

async function launchBrowser(executable) {
  const profile = mkdtempSync(join(tmpdir(), "harness-ui-"));
  const child = spawn(
    executable,
    ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
      // a throwaway profile must never touch the user's keychain (macOS "Keychain Not Found" prompts)
      "--use-mock-keychain", "--password-store=basic", "about:blank"],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  const endpoint = await new Promise((resolve, reject) => {
    let log = "";
    const timer = setTimeout(() => reject(new Error("browser did not report a debugging port in 15s")), 15000);
    child.stderr.on("data", (chunk) => {
      log += chunk;
      const match = /DevTools listening on (ws:\/\/\S+)/.exec(log);
      if (match) {
        clearTimeout(timer);
        resolve(match[1]);
      }
    });
    child.on("exit", () => reject(new Error("browser exited before it was ready")));
  });
  const close = async () => {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    child.kill();
    await exited;
    rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
  };
  return { child, endpoint, close };
}

function connect(url) {
  const socket = new WebSocket(url);
  let nextId = 1;
  const pending = new Map();
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
    }
  });
  const opened = new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve);
    socket.addEventListener("error", () => reject(new Error("could not connect to the browser")));
  });
  const send = (method, params = {}, sessionId) =>
    new Promise((resolve, reject) => {
      const id = nextId++;
      pending.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
  return { opened, send, close: () => socket.close() };
}

// Runs inside the page. Returns plain findings; the reviewer decides what matters for the audience.
function pageChecks() {
  const findings = [];
  const add = (check, wcag, detail) => findings.push({ check, wcag, detail });
  const label = (el) => `${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ""}${el.className && typeof el.className === "string" ? `.${el.className.trim().split(/\s+/).slice(0, 2).join(".")}` : ""}`;
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none";
  };

  const doc = document.documentElement;
  if (doc.scrollWidth > doc.clientWidth + 1) add("horizontal-scroll", "1.4.10 Reflow", `page is ${doc.scrollWidth}px wide in a ${doc.clientWidth}px viewport`);
  if (!doc.lang) add("html-lang", "3.1.1 Language of Page", "<html> has no lang attribute");
  if (!document.title.trim()) add("page-title", "2.4.2 Page Titled", "document has no title");
  if (!document.querySelector("meta[name=viewport]")) add("viewport-meta", "1.4.4 Resize Text", "no <meta name=viewport>; mobile browsers render a desktop layout");
  if (document.querySelectorAll("h1").length !== 1) add("h1-count", "1.3.1 Info and Relationships", `${document.querySelectorAll("h1").length} <h1> elements, expected 1`);
  if (!document.querySelector("main, [role=main]")) add("main-landmark", "1.3.1 Info and Relationships", "no <main> landmark");

  for (const img of document.querySelectorAll("img")) {
    if (!img.hasAttribute("alt")) add("img-alt", "1.1.1 Non-text Content", `${label(img)} has no alt attribute (use alt="" when decorative)`);
  }

  const interactive = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [tabindex]:not([tabindex='-1'])")].filter(visible);
  for (const el of interactive) {
    const r = el.getBoundingClientRect();
    const text = (el.textContent || "").trim();
    if (r.width < 24 || r.height < 24) add("target-size-min", "2.5.8 Target Size (Minimum)", `${label(el)} "${text.slice(0, 30)}" is ${Math.round(r.width)}x${Math.round(r.height)}px, below 24x24`);
    else if (innerWidth < 768 && (r.width < 44 || r.height < 44)) add("target-size-touch", "2.5.5 Target Size (Enhanced)", `${label(el)} "${text.slice(0, 30)}" is ${Math.round(r.width)}x${Math.round(r.height)}px, below the 44x44 touch guideline`);
    const named = text || el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title") || el.querySelector("img[alt]:not([alt=''])");
    if (!named && ["A", "BUTTON"].includes(el.tagName)) add("accessible-name", "4.1.2 Name, Role, Value", `${label(el)} has no text or aria-label`);
  }

  for (const field of document.querySelectorAll("input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea")) {
    if (!visible(field)) continue;
    const labelled = field.labels?.length || field.getAttribute("aria-label") || field.getAttribute("aria-labelledby");
    if (!labelled) add("field-label", "3.3.2 Labels or Instructions", `${label(field)} has no <label> or aria-label`);
  }

  // Contrast: text colour against the nearest opaque background. Approximate (no images or gradients); axe is the exact check.
  const parse = (css) => {
    const m = css.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const [r, g, b, a = 1] = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return { r, g, b, a };
  };
  const luminance = ({ r, g, b }) => {
    const [R, G, B] = [r, g, b].map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * R + 0.7152 * G + 0.0722 * B;
  };
  const backdrop = (el) => {
    for (let node = el; node; node = node.parentElement) {
      const bg = parse(getComputedStyle(node).backgroundColor);
      if (bg && bg.a === 1) return bg;
    }
    return { r: 255, g: 255, b: 255, a: 1 };
  };
  const seen = new Set();
  for (const el of document.querySelectorAll("body *")) {
    if (!visible(el) || ![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
    const style = getComputedStyle(el);
    const fg = parse(style.color);
    if (!fg || fg.a < 1) continue;
    const [L1, L2] = [luminance(fg), luminance(backdrop(el))].sort((a, b) => b - a);
    const ratio = (L1 + 0.05) / (L2 + 0.05);
    const px = Number.parseFloat(style.fontSize);
    const large = px >= 24 || (px >= 18.66 && Number(style.fontWeight) >= 700);
    const need = large ? 3 : 4.5;
    const key = `${style.color}|${label(el)}`;
    if (ratio < need && !seen.has(key)) {
      seen.add(key);
      add("contrast", "1.4.3 Contrast (Minimum)", `${label(el)} "${el.textContent.trim().slice(0, 30)}" is ${ratio.toFixed(2)}:1, needs ${need}:1`);
    }
    if (px < 12) add("small-text", "1.4.4 Resize Text", `${label(el)} text is ${px}px`);
  }
  return findings;
}

async function run() {
  const options = parseArgs(process.argv.slice(2));
  const urls = options.urls.map((u) => checkUrl(u, options.allowRemote));
  const viewports = parseViewports(options.viewports);
  const schemes = options.scheme === "both" ? ["light", "dark"] : [options.scheme];
  const axeSource = loadAxe();
  const pruned = options.out ? null : pruneRuns(options["keep-days"], options["max-mb"]);
  if (!options.out) options.out = join(SHOTS_ROOT, repoName(), new Date().toISOString().replace(/[:.]/g, "-"));
  mkdirSync(options.out, { recursive: true });

  const browser = await launchBrowser(findBrowser());
  const cdp = connect(browser.endpoint);
  const report = { axe: axeSource ? "run" : "not run: axe-core is not installed in this repo", shots: [] };
  try {
    await cdp.opened;
    const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
    const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
    const page = (method, params) => cdp.send(method, params, sessionId);
    await page("Page.enable");
    await page("Network.setCacheDisabled", { cacheDisabled: true });

    for (const [index, url] of urls.entries()) {
      const prefix = options.name || "page";
      const name = urls.length > 1 || !options.name ? `${prefix}-${index + 1}` : prefix;
      for (const scheme of schemes) {
        await page("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: scheme }] });
        for (const viewport of viewports) {
          await page("Emulation.setDeviceMetricsOverride", { ...viewport, deviceScaleFactor: options.scale });
          await page("Page.navigate", { url });
          await new Promise((resolve) => setTimeout(resolve, options.wait));
          const evaluate = async (expression) => {
            const { result, exceptionDetails } = await page("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
            if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? "page script failed");
            return result.value;
          };
          const findings = await evaluate(`(${pageChecks.toString()})()`);
          if (axeSource) {
            const violations = await evaluate(`(async () => { ${axeSource}; const r = await axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] }); return r.violations.map(v => ({ check: "axe:" + v.id, wcag: v.tags.filter(t => t.startsWith("wcag")).join(" "), detail: v.help + " (" + v.nodes.length + " nodes, first: " + (v.nodes[0]?.target?.join(" ") ?? "") + ")" })); })()`);
            findings.push(...violations);
          }
          let clip;
          if (options.fullPage) {
            const { contentSize } = await page("Page.getLayoutMetrics");
            clip = { x: 0, y: 0, width: contentSize.width, height: Math.min(contentSize.height, 8000), scale: 1 };
          }
          const shot = await page("Page.captureScreenshot", { format: "png", clip });
          const file = join(options.out, `${name}-${viewport.width}x${viewport.height}${scheme === "dark" ? "-dark" : ""}.png`);
          writeFileSync(file, Buffer.from(shot.data, "base64"));
          report.shots.push({ file, url, viewport: `${viewport.width}x${viewport.height}`, scheme, findings });
        }
      }
    }
  } finally {
    cdp.close();
    await browser.close();
  }
  writeFileSync(join(options.out, "report.json"), JSON.stringify(report, null, 2));

  const grouped = new Map();
  for (const shot of report.shots) {
    console.log(`${shot.file}  (${shot.findings.length} findings)`);
    for (const f of shot.findings) {
      const key = `[${f.check}] WCAG ${f.wcag}: ${f.detail}`;
      const where = `${shot.viewport}${shot.scheme === "dark" ? " dark" : ""}`;
      grouped.set(key, [...(grouped.get(key) ?? []), where]);
    }
  }
  console.log("\nFindings, each with the viewports where it occurs:");
  for (const [finding, where] of grouped) console.log(`  ${finding}  @ ${where.length === report.shots.length ? "all" : where.join(", ")}`);
  console.log(`axe-core: ${report.axe}`);
  if (pruned) console.log(`cleanup: removed ${pruned.removed} old run(s), freed ${pruned.freedMb} MB (kept ${options["keep-days"]} days, max ${options["max-mb"]} MB)`);
  console.log(`report: ${join(options.out, "report.json")}`);
}

try {
  await run();
} catch (error) {
  fail(error.message);
}
