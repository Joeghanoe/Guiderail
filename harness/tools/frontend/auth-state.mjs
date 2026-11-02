// Auth state for screenshot.mjs: lets the tool capture a page that sits behind a login without driving the login screen.
//
// The state file is plain data, produced out of band (see auth-examples/): a token is fetched server-side, then written as the
// browser storage the app reads on boot (an MSAL cache in sessionStorage, a session in localStorage, a cookie). The tool puts it
// into the page before any page script runs. This is the pattern a repo's Cypress `cy.session` login uses; the tool needs no
// Cypress and no test account in the login UI.
//
// File format (JSON). Every key is optional; unknown keys are refused:
//   { "origin": "http://localhost:5173",        // where it applies; default: the origin of the first --url
//     "clear": true,                            // clear the listed storage areas first (default true), so no stale state bleeds in
//     "sessionStorage": { "<key>": "<string>" },
//     "localStorage":   { "<key>": "<string>" },
//     "cookies": [ { "name": "...", "value": "...", "path": "/", "httpOnly": false, "secure": false, "sameSite": "Lax" } ] }
//
// Safety (SEC.1, SEC.2): the file is data, never code. Values are never printed or written to report.json (only key counts).
// The storage script runs only in the top frame of the named origin, so a token is never offered to another site. screenshot.mjs
// refuses a file that sits unignored inside a git repository.

const ALLOWED = new Set(["origin", "clear", "sessionStorage", "localStorage", "cookies"]);
const COOKIE_KEYS = new Set(["name", "value", "path", "httpOnly", "secure", "sameSite"]);
const MAX_ENTRIES = 200;
const MAX_VALUE = 64 * 1024;

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function checkStorage(area, value) {
  if (!isPlainObject(value)) throw new Error(`auth state: ${area} must be an object of string values`);
  const entries = Object.entries(value);
  if (entries.length > MAX_ENTRIES) throw new Error(`auth state: ${area} has more than ${MAX_ENTRIES} entries`);
  for (const [key, entry] of entries) {
    if (typeof entry !== "string") throw new Error(`auth state: ${area} value for key "${key}" is not a string`);
    if (entry.length > MAX_VALUE) throw new Error(`auth state: ${area} value for key "${key}" is larger than ${MAX_VALUE} characters`);
  }
  return value;
}

/** Validates parsed JSON and returns the normalised state. Error messages name keys, never values. */
export function parseAuthState(text) {
  let raw;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new Error("auth state: the file is not valid JSON");
  }
  if (!isPlainObject(raw)) throw new Error("auth state: the file must contain a JSON object");
  for (const key of Object.keys(raw)) if (!ALLOWED.has(key)) throw new Error(`auth state: unknown key "${key}" (allowed: ${[...ALLOWED].join(", ")})`);
  if (raw.origin !== undefined) {
    let origin;
    try {
      origin = new URL(raw.origin);
    } catch {
      throw new Error("auth state: origin is not a URL");
    }
    if (!["http:", "https:"].includes(origin.protocol)) throw new Error("auth state: origin must be http or https");
  }
  if (raw.clear !== undefined && typeof raw.clear !== "boolean") throw new Error("auth state: clear must be true or false");
  const state = {
    origin: raw.origin ? new URL(raw.origin).origin : undefined,
    clear: raw.clear !== false,
    sessionStorage: raw.sessionStorage === undefined ? {} : checkStorage("sessionStorage", raw.sessionStorage),
    localStorage: raw.localStorage === undefined ? {} : checkStorage("localStorage", raw.localStorage),
    cookies: [],
  };
  if (raw.cookies !== undefined) {
    if (!Array.isArray(raw.cookies) || raw.cookies.length > MAX_ENTRIES) throw new Error("auth state: cookies must be a list of at most 200 cookies");
    for (const [i, cookie] of raw.cookies.entries()) {
      if (!isPlainObject(cookie)) throw new Error(`auth state: cookie ${i} is not an object`);
      for (const key of Object.keys(cookie)) if (!COOKIE_KEYS.has(key)) throw new Error(`auth state: cookie ${i} has unknown key "${key}"`);
      if (typeof cookie.name !== "string" || !cookie.name || typeof cookie.value !== "string") throw new Error(`auth state: cookie ${i} needs a string name and value`);
      if (cookie.value.length > MAX_VALUE) throw new Error(`auth state: cookie "${cookie.name}" is larger than ${MAX_VALUE} characters`);
      if (cookie.sameSite !== undefined && !["Strict", "Lax", "None"].includes(cookie.sameSite)) throw new Error(`auth state: cookie "${cookie.name}" sameSite must be Strict, Lax or None`);
      state.cookies.push({ path: "/", httpOnly: false, secure: false, ...cookie });
    }
  }
  const total = Object.keys(state.sessionStorage).length + Object.keys(state.localStorage).length + state.cookies.length;
  if (total === 0) throw new Error("auth state: the file seeds nothing (no sessionStorage, localStorage or cookies)");
  return state;
}

/**
 * The script the browser runs before any page script on every navigation. It does nothing unless it is the top frame of `origin`.
 * Storage is cleared first (when asked) and then seeded, so a run never depends on what an earlier run left behind.
 */
export function seedScript(state, origin) {
  const payload = JSON.stringify({ origin, clear: state.clear, sessionStorage: state.sessionStorage, localStorage: state.localStorage });
  return `(() => {
  const state = ${payload};
  if (window.top !== window || location.origin !== state.origin) return;
  for (const area of ["sessionStorage", "localStorage"]) {
    const entries = state[area];
    if (!Object.keys(entries).length) continue;
    try {
      if (state.clear) window[area].clear();
      for (const [key, value] of Object.entries(entries)) window[area].setItem(key, value);
    } catch {
      /* storage can be blocked; the page then renders as logged out and the capture shows it */
    }
  }
})();`;
}

/** What the report may say about the state: counts and the origin, never a key or a value. */
export function describeAuthState(state, origin) {
  return {
    origin,
    sessionStorageKeys: Object.keys(state.sessionStorage).length,
    localStorageKeys: Object.keys(state.localStorage).length,
    cookies: state.cookies.length,
    cleared: state.clear,
  };
}

/** CDP Network.setCookie parameters for the origin. */
export function cookieParams(state, origin) {
  return state.cookies.map((c) => ({ url: origin, name: c.name, value: c.value, path: c.path, httpOnly: c.httpOnly, secure: c.secure, ...(c.sameSite ? { sameSite: c.sameSite } : {}) }));
}
