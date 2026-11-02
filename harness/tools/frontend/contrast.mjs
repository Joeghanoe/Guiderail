#!/usr/bin/env node
// Checks the colour tokens of a style guide against WCAG 2.2 contrast (1.4.3) before any screen is built from them (UI.1).
// A style guide can ship a colour pair that fails AA: the FoodApp portal's guide suggested white on #3F8A2E (4.3:1) as the accessible
// button green, and used the brand orange #D9661F (3.9:1) for links. This reads the tokens and says so up front.
//
// Usage: node contrast.mjs [--css <file>] --pair <fg>/<bg> [--pair ...] [--large <fg>/<bg> ...] [--list]
//   --css     a stylesheet or markdown file with custom properties (`--color-orange: #d9661f;`); tokens are the first value found
//   --pair    small text: foreground/background, each a token name (`--color-orange` or `color-orange`) or a hex colour; needs 4.5:1
//   --large   large text (24 px, or 18.66 px bold) and UI components: needs 3:1
//   --list    print every token with its contrast against white and black
// Exit 0 when every pair passes, 1 when one fails or a token is unknown. Reads one file; runs nothing.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

function fail(message) {
  console.error(`contrast.mjs: ${message}`);
  process.exit(1);
}

export function parseColor(value) {
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value.trim());
  if (!hex) return null;
  const full = hex[1].length === 3 ? [...hex[1]].map((c) => c + c).join("") : hex[1];
  return [0, 2, 4].map((i) => Number.parseInt(full.slice(i, i + 2), 16));
}

function luminance([r, g, b]) {
  const [R, G, B] = [r, g, b].map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

export function ratio(foreground, background) {
  const [bright, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (bright + 0.05) / (dark + 0.05);
}

/** Custom properties with a hex value. The first declaration of a name wins, so a dark-scheme override is not mistaken for the token. */
export function readTokens(text) {
  const tokens = new Map();
  for (const match of text.matchAll(/(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b/g)) {
    if (!tokens.has(match[1])) tokens.set(match[1], match[2]);
  }
  return tokens;
}

function resolve(side, tokens) {
  const name = side.startsWith("--") ? side : `--${side}`;
  const value = tokens.get(name) ?? (parseColor(side) ? side : null);
  const color = value && parseColor(value);
  if (!color) fail(`unknown colour "${side}" (not a token in the file and not a hex value)`);
  return { label: tokens.has(name) ? `${name} ${value}` : value, color };
}

export function check(pairs, tokens) {
  return pairs.map(({ fg, bg, large }) => {
    const a = resolve(fg, tokens);
    const b = resolve(bg, tokens);
    const need = large ? 3 : 4.5;
    const got = ratio(a.color, b.color);
    return { text: `${a.label} on ${b.label}`, large, need, got, ok: got >= need };
  });
}

function main(argv) {
  const pairs = [];
  let css = "";
  let list = false;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--css") css = argv[++i] ?? fail("--css needs a file");
    else if (arg === "--list") list = true;
    else if (arg === "--pair" || arg === "--large") {
      const [fg, bg, ...rest] = (argv[++i] ?? "").split("/");
      if (!fg || !bg || rest.length) fail(`${arg} needs <foreground>/<background>`);
      pairs.push({ fg, bg, large: arg === "--large" });
    } else fail(`unknown option ${arg}`);
  }
  let tokens = new Map();
  if (css) {
    try {
      tokens = readTokens(readFileSync(css, "utf8"));
    } catch (error) {
      fail(`cannot read ${css}: ${error.message}`);
    }
  }
  if (!pairs.length && !list) fail("give at least one --pair or --large, or --list");
  if (list) {
    for (const [name, value] of tokens) {
      const color = parseColor(value);
      console.log(`${name.padEnd(28)} ${value}  on white ${ratio(color, [255, 255, 255]).toFixed(2)}:1  on black ${ratio(color, [0, 0, 0]).toFixed(2)}:1`);
    }
  }
  const results = check(pairs, tokens);
  for (const r of results) console.log(`${r.ok ? "pass" : "FAIL"}  ${r.got.toFixed(2)}:1 (needs ${r.need}:1${r.large ? ", large text" : ""})  ${r.text}`);
  return results.every((r) => r.ok) ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) process.exit(main(process.argv.slice(2)));
