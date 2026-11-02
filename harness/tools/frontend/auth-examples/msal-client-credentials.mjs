#!/usr/bin/env node
// Example producer of an auth state file for an app that signs in with MSAL (Azure AD / Entra ID). It is the pattern of
// TeamNOW.Aquarium.Portal/cypress/support/commands.ts, without Cypress: fetch a token server-side with the client-credentials flow
// (no test user, no login UI), then write the MSAL v5 browser cache entries the app reads on boot into a state file for
// `screenshot.mjs --auth-state`.
//
// Usage: node msal-client-credentials.mjs --out <state.json> [--origin http://localhost:5173]
// Reads (from the environment of this process, never from a file in the repo; SEC.2):
//   AAD_TENANT_ID, AAD_CLIENT_ID, AAD_CLIENT_SECRET   the app registration the portal's role comes from
//   AAD_SCOPE   optional, default "<client id>/.default"
// Put --out outside the repo or in .gitignore: it holds a live token. screenshot.mjs refuses it otherwise.
//
// Status: the cache layout is the one the Aquarium portal's Cypress login uses with MSAL v5 ("|" separated, lower-cased keys). This
// example has not been run against a real tenant by the harness; a repo on another MSAL major version checks the key layout first.
import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const SEP = "|"; // MSAL v5 separates cache key parts with "|" (older versions used "-")
const ENVIRONMENT = "login.windows.net";

const b64url = (value) => Buffer.from(typeof value === "string" ? value : JSON.stringify(value)).toString("base64url");

/** An unsigned JWT. MSAL reads idTokenClaims from the cache without re-validating the signature. */
export const fakeIdToken = (claims) => `${b64url({ alg: "none", typ: "JWT" })}.${b64url(claims)}.`;

export function decodeClaims(jwt) {
  const part = jwt.split(".")[1];
  if (!part) throw new Error("the access token is not a JWT");
  return JSON.parse(Buffer.from(part, "base64url").toString("utf8"));
}

/** Pure: a token response in, the sessionStorage entries MSAL needs out. */
export function buildMsalSessionStorage({ accessToken, expiresIn, extExpiresIn = expiresIn, clientId, now = Date.now() }) {
  const claims = decodeClaims(accessToken);
  const { oid, tid } = claims;
  if (!oid || !tid) throw new Error("the token has no oid or tid claim");
  const homeAccountId = `${oid}.${tid}`;
  const scope = `${clientId}/.default`;
  const nowSeconds = Math.floor(now / 1000);
  const key = (...parts) => parts.join(SEP).toLowerCase();
  const accountKey = key("msal.2", homeAccountId, ENVIRONMENT, tid);
  const idKey = key("msal.2", homeAccountId, ENVIRONMENT, "idtoken", clientId, tid, "", "");
  const accessKey = key("msal.2", homeAccountId, ENVIRONMENT, "accesstoken", clientId, tid, scope, "", "");
  const name = "E2E Service Principal";
  return {
    "msal.2.account.keys": JSON.stringify([accountKey]),
    [accountKey]: JSON.stringify({ homeAccountId, environment: ENVIRONMENT, realm: tid, localAccountId: oid, username: "e2e-service-principal", authorityType: "MSSTS", name, lastUpdatedAt: String(now) }),
    [`msal.2.token.keys.${clientId}`]: JSON.stringify({ idToken: [idKey], accessToken: [accessKey], refreshToken: [] }),
    [idKey]: JSON.stringify({
      homeAccountId, environment: ENVIRONMENT, credentialType: "IdToken", realm: tid, clientId, lastUpdatedAt: String(now),
      secret: fakeIdToken({ oid, sub: oid, tid, roles: claims.roles ?? [], preferred_username: "e2e-service-principal", name }),
    }),
    [accessKey]: JSON.stringify({
      homeAccountId, environment: ENVIRONMENT, credentialType: "AccessToken", secret: accessToken, realm: tid, target: scope, clientId,
      cachedAt: String(nowSeconds), expiresOn: String(nowSeconds + expiresIn), extendedExpiresOn: String(nowSeconds + extExpiresIn), tokenType: "Bearer", lastUpdatedAt: String(now),
    }),
    [`msal.${clientId}.active-account-filters`]: JSON.stringify({ homeAccountId, localAccountId: oid, tenantId: tid }),
  };
}

async function fetchToken({ tenantId, clientId, clientSecret, scope }) {
  const response = await fetch(`https://login.microsoftonline.com/${encodeURIComponent(tenantId)}/oauth2/v2.0/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ grant_type: "client_credentials", client_id: clientId, client_secret: clientSecret, scope }),
  });
  if (!response.ok) throw new Error(`token request failed with status ${response.status}`); // never print the body: it can echo the request
  const body = await response.json();
  return { accessToken: body.access_token, expiresIn: Number(body.expires_in), extExpiresIn: Number(body.ext_expires_in ?? body.expires_in) };
}

async function main() {
  const args = process.argv.slice(2);
  const value = (flag) => (args.includes(flag) ? args[args.indexOf(flag) + 1] : undefined);
  const out = value("--out");
  if (!out) throw new Error("--out <state.json> is required");
  const need = (name) => process.env[name] || (() => { throw new Error(`${name} is not set`); })();
  const clientId = need("AAD_CLIENT_ID");
  const token = await fetchToken({ tenantId: need("AAD_TENANT_ID"), clientId, clientSecret: need("AAD_CLIENT_SECRET"), scope: process.env.AAD_SCOPE || `${clientId}/.default` });
  const state = { ...(value("--origin") ? { origin: value("--origin") } : {}), clear: true, sessionStorage: buildMsalSessionStorage({ ...token, clientId }) };
  writeFileSync(out, JSON.stringify(state), { mode: 0o600 });
  console.log(`wrote ${out} (${Object.keys(state.sessionStorage).length} sessionStorage keys; token not shown)`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main().catch((error) => {
    console.error(`msal-client-credentials.mjs: ${error.message}`);
    process.exit(1);
  });
}
