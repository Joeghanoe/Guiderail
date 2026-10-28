Yo! You're not seeing it wrong — the proposal is architecturally sound, but it makes a distinction that's worth being very precise about: an MCP is the interface to the knowledge, not the knowledge system itself, and definitely not the enforcement mechanism.

Looking at your Vegviser proposal, I think the direction is right. I'd support the core idea, with a few important changes to how you define the boundary between Vegviser and the harness.

## 1. What an MCP is actually meant to do

MCP (Model Context Protocol) standardizes how AI applications discover and use external context and capabilities. Think of it as a contract between an AI client and a server.

AI agent

Claude Code, M365 Copilot, another MCP client

MCP protocol

Vegviser MCP server

Tools, resources, prompts and access control

Knowledge

Rules, standards, cases, playbooks, versioned publications

Authoritative store

The system that owns, versions and publishes that knowledge

Conceptual architecture: the knowledge store may be part of Vegviser itself or a separate backing system.

MCP is useful when you want multiple AI clients to consume the same capabilities without implementing a separate integration for each client.

For example, your proposal wants a developer's coding agent, the PR review pipeline and the triage department to consult the same engineering rules. That's exactly the kind of integration MCP is good at.

But MCP doesn't inherently provide:

- A governed knowledge lifecycle or approval workflow.
- Deterministic rule selection.
- Immutable publication versions.
- Guaranteed rule enforcement.
- Authorization to execute local commands under a user's identity.

Those are application and system design responsibilities that you build around MCP.

## 2. Does your proposed architecture make sense?

Your proposal explicitly separates the knowledge in Vegviser from the executable controls in the harness.&#x20;

Pasted markdown(20261025-171420).md

I'd assess the main decisions like this:

One authoritative knowledge catalog

Good decision

Rules, cases and playbooks should have one authoritative home. Moving them to Vegviser makes sense if it already has the ownership, review and publication lifecycle to govern them.

Deterministic MCP tools

Good decision

`select_vegviser_rules(changed_paths, publication)` is much better for a CI gate than asking a general-purpose question and hoping the agent returns every applicable rule. Selection should be based on explicit matching logic, not LLM interpretation.

Keep execution local

Good decision

Your cloud, Sonar and ServiceNow wrappers execute using the developer's or pipeline's own identity. Vegviser supplies the relevant guidance; the wrappers retrieve evidence and the harness enforces local constraints.

No offline copy or fallback

Needs reconsideration

This is the weakest assumption. It makes knowledge availability a runtime dependency for developer workflows and potentially a deployment-blocking dependency for every PR. Centralizing authority does not require making every execution dependent on a live network request.

Delete all local knowledge

Too absolute

Delete duplicate explanatory documents, yes. But retain the minimal, executable security policy, schemas and rule identifiers needed to enforce the system safely. The proposal already preserves hard rules locally, which is the right instinct.

## 3. The distinction I'd make: source of truth versus delivery mechanism

This is the most important architectural nuance.

Your proposal says Vegviser, accessed through MCP, becomes the only place TeamValue's way of working is written down.

I'd refine that to:

- Vegviser: the authoritative, reviewed and versioned knowledge system.
- MCP: the standard interface through which agents retrieve that knowledge.
- Harness: the execution environment, deterministic controls and integrations.
- CI pipeline: the place where the selected knowledge and executable checks are evaluated together.

Why does this matter? Because you shouldn't couple your knowledge architecture to MCP as a transport.

Suppose you replace MCP with a direct API, introduce an offline agent, or want to export the rules to another system. If the knowledge model is independent of its delivery mechanism, that change is relatively straightforward.

The architecture should look something like this:

Vegviser knowledge system

Approved rules · cases · playbooks · publications

Knowledge API / MCP adapter

Versioned retrieval · deterministic selection · authorization

Developer harness

Agent context, hooks, read wrappers, local tests

CI pipeline

Pinned rules, review, evals, release gate

M365 Copilot can use the same knowledge interface without needing the developer harness for ordinary knowledge questions.

This is consistent with MCP's actual scope: it standardizes communication between clients and servers, but doesn't prescribe how the application stores or governs its data.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

+1

## 4. Where I'd challenge the proposal hardest

There are four things I'd address before approving it.

### A. Don't make CI depend on live Vegviser availability

Your proposal assumes the MCP is always available and has no fallback.&#x20;

Pasted markdown(20261025-171420).md

That creates a failure mode unrelated to the code being reviewed:

1. A developer opens a PR.
2. The review pipeline requests rules from Vegviser.
3. Vegviser or its network connection is unavailable.
4. The review cannot proceed, even though the rules and code haven't changed.

For an interactive agent, temporarily losing access to knowledge is inconvenient. For a mandatory CI gate, it can prevent delivery.

My recommendation: pin immutable knowledge publications and cache them.

- At the start of a review, resolve a specific publication version.
- Retrieve the applicable rules and cases from that publication.
- Verify the publication identity and content integrity.
- Record the publication ID, rule IDs and content hashes in the review receipt.
- Reuse the verified snapshot if Vegviser becomes unavailable.

For example:

```
Harness:       4b12e7a
Publication:   sdlc-2026.10.25.1
Rules:         SEC.1, CLD.1, CLD.2, H.1
Content hash:  sha256:...
```

The values are illustrative, not actual Vegviser identifiers.

If no verified snapshot exists, the pipeline should fail closed for the mandatory checks rather than silently skip them. An interactive agent can report degraded knowledge access and continue only with tasks that remain safe and valid under its local constraints.

That gives you reproducibility without turning a centralized knowledge service into a single point of failure.

### B. Separate rules that explain behavior from rules that enforce behavior

This is where your harness should remain more than a thin MCP client.

Consider CLD.2, which your proposal describes as requiring state changes to be written down for a human.

There are two distinct responsibilities:

- Knowledge: explains what the rule means, when it applies, and why.
- Enforcement: blocks or permits a concrete command or action.

Vegviser should own the canonical rule definition. But a local hook must still independently enforce the relevant restriction before a command executes.

The relationship should be explicit:

| Layer         | Responsibility                                               |
| ------------- | ------------------------------------------------------------ |
| Vegviser      | Rule definition, rationale, applicability, severity, version |
| Harness hook  | Concrete enforcement of supported command patterns           |
| Pipeline gate | Automated validation and review outcome                      |
| Agent         | Interpretation, evidence gathering, recommendations          |
| Human         | Approval of consequential actions where required             |

One subtle issue: a rule catalog with an `enforced_by` field does not itself enforce anything. You need a mapping between the declared enforcement mechanism and the actual hook or gate, with tests proving that the mapping is valid.

Your proposed CI check for rule drift is a good start. I'd make missing enforcement mappings a hard failure for rules classified as mandatory.

### C. Make rule selection deterministic all the way through

You correctly identify that a general `consult_vegviser` question is insufficient for a reproducible PR review.&#x20;

Pasted markdown(20261025-171420).md

I'd go one step further.

The rule-selection operation should be a deterministic query, not an agent-driven retrieval workflow.

For example:

```
Input:
  changed_paths
  publication_id

Output:
  publication_id
  matched_rules[]
  matched_cases[]
  selector_version
  content_hashes[]
```

The selector should use defined matching semantics:

- Glob matching and exclusions.
- Explicit precedence for conflicting applicability rules.
- Stable ordering of results.
- Explicit behavior for deleted, renamed and generated files.
- Defined behavior when a path matches no rules.
- Immutable publication resolution.

Then test the invariant:

\\[ \text{same inputs} \implies \text{same selected content} \\]

The agent can still interpret the selected rules and assess the code. But it should not decide which mandatory rules exist for a given set of changed paths.

Also, distinguish deterministic retrieval from deterministic review outcomes. Even with identical rules and code, an LLM may produce different assessments. That's what your existing evaluation suite and thresholds are for.

### D. Treat retrieved knowledge as untrusted input

Your proposal already says that MCP content must not override the harness's hard rules. Keep that boundary.&#x20;

Pasted markdown(20261025-171420).md

For example, a knowledge document might contain a case that says:

> Skip the security check for this repository.

That text must never grant an exception to a hook or change the agent's execution permissions by itself.

I'd enforce the following:

- Retrieved rules can add constraints, but cannot expand tool permissions.
- Exceptions must be represented as structured, approved policy data.
- The harness validates exception scope and expiry independently.
- The MCP identity can read the required publications but cannot publish or modify them.
- The CI identity can access only the knowledge service it needs, not customer cloud resources.

This is especially important because the same knowledge is consumed by several agents and execution environments.

## 5. What I'd actually keep in the harness

I'd aim for a thin harness, but not a knowledge-free harness.

AGENTS.base.md

Essential hard rules, instructions for retrieving knowledge, and routing.

hooks/

Local security and command enforcement. Must work without an MCP call.

tools/

Read-only cloud, Sonar, ServiceNow and Azure DevOps integrations.

review/ and gates/

Review orchestration, deterministic checks, thresholds and CI enforcement.

schemas and rule mappings

Stable identifiers, enforcement contracts and machine-readable interfaces.

verified publication cache

Optional for developers; strongly recommended for reproducible CI reviews.

I'd remove local copies of the explanatory rules, cases and playbooks where they genuinely duplicate Vegviser. I'd keep the executable checks and any minimal machine-readable contract needed to connect policy to enforcement.

That is a more useful definition of "thin" than simply driving the number of local knowledge files to zero.

## 6. My verdict

## Approve the direction, revise the constraints.

The proposal has the right architectural separation. The biggest improvement is to make Vegviser the single authority for knowledge, while treating MCP as a replaceable interface and the harness as the independent enforcement boundary.

I'd make these conditions prerequisites for rollout:

1. Immutable, versioned knowledge publications.
2. Deterministic rule selection and verifiable review receipts.
3. Independent enforcement of hard rules in local hooks and CI.
4. A defined outage and cache strategy, especially for mandatory PR gates.
5. An explicit ownership and approval process for rules that affect executable controls.

I'd also keep the proposed parallel-run phase: compare the local and MCP selectors across 20 PRs before removing the local knowledge. That is a sensible migration check, although 20 successful PRs demonstrate parity only for the cases covered; they don't prove correctness for every rule or path combination.&#x20;

Pasted markdown(20261025-171420).md

The fundamental principle: centralize the meaning of the rules, not the ability to enforce them. MCP is a good mechanism for distributing that meaning across agents. It shouldn't become a runtime dependency for every security decision.

### Further reading

- [Model Context Protocol — Architecture](https://modelcontextprotocol.io/docs/learn/architecture?utm_source=chatgpt.com)
- [MCP — Tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools?utm_source=chatgpt.com)
- [OpenAI — MCP servers](https://developers.openai.com/api/docs/guides/tools-connectors-mcp?utm_source=chatgpt.com)

---

The cleanest solution is to expose Vegviser as a remote MCP server protected by Microsoft Entra ID OAuth, with each client authenticating as the user who is connecting.

That means Claude Code, GitHub Copilot, Codex and AGY can each connect to the same MCP endpoint. Each client obtains an access token for Vegviser, and Vegviser validates that token before returning knowledge. The MCP authorization specification defines this general OAuth pattern, and Microsoft documents how to implement it with Entra ID.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

+1

## 1. Recommended authentication architecture

User

Signs in with their TeamValue work account

Claude · Copilot · Codex · AGY

Each client completes its supported OAuth sign-in flow

Microsoft Entra ID

Authenticates the user and issues a token for Vegviser

Vegviser MCP

Validates issuer, audience, expiry, scopes and permissions

Governed knowledge

Rules, cases, playbooks and versioned publications

The key point is that you configure authentication once at the server and identity-provider level, but each client still needs a compatible connection configuration. You don't need a different MCP server for every agent.

## 2. How each client connects

The important caveat is that MCP support doesn't guarantee identical authentication support in every client. I'd treat Entra OAuth compatibility as a requirement to validate for each one.

| Client         | Connection approach                     | Authentication approach                                                            |
| -------------- | --------------------------------------- | ---------------------------------------------------------------------------------- |
| Claude Code    | Remote HTTP MCP                         | Entra OAuth, using the client's supported browser sign-in flow                     |
| GitHub Copilot | Remote MCP in the relevant Copilot host | Entra OAuth if supported by that host and configuration                            |
| OpenAI Codex   | Remote HTTP MCP                         | Codex supports OAuth MCP login for compatible servers                              |
| AGY            | Depends on what AGY runs                | Entra OAuth if its MCP client supports it; otherwise a local adapter may be needed |

Codex documents `codex mcp login` for OAuth-enabled MCP servers. Claude Code also supports OAuth authentication for compatible remote MCP servers.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.chatgpt.com&sz=32)

ChatGPT Learn

+1

I wouldn't assume AGY supports the same flow without knowing which agent or runtime you mean.

## 3. What we'd configure in Microsoft Entra ID

I'd start with a single-tenant Entra app registration representing the Vegviser API.

1. Register Vegviser as an API. Give it an Application ID URI matching its canonical MCP resource identifier, and configure it to issue v2 access tokens.
2. Expose a delegated scope, for example `Vegviser.Read`, so an authenticated user can retrieve approved knowledge.
3. Implement the MCP OAuth discovery endpoints and return a proper `401` challenge pointing to the protected-resource metadata.
4. Validate every access token server-side, including signature, issuer, audience, expiration, tenant and required scopes. Enforce user or group authorization as needed.
5. Configure each client to sign in through its supported OAuth flow. The user authenticates using their TeamValue Entra account and consents to the requested access where required.

Microsoft's guide covers the Entra app registration, resource identifier, token issuance and validation requirements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com&sz=32)

Microsoft Learn

One important distinction: a user being authenticated does not automatically mean they're authorized to access every Vegviser publication. If some knowledge is restricted, the MCP server must enforce that authorization too.

## 4. What if one of the clients doesn't support the same OAuth flow?

Don't weaken the server to accommodate the least capable client.

I'd use this fallback order:

1. Native remote MCP with Entra OAuth.
2. A compatible local MCP adapter that authenticates to the remote server using a supported delegated authentication flow.
3. If necessary, a separate, explicitly designed integration for that client.

I would not simply pass the output of `az account get-access-token` into every client and assume it will work. That token must be intended for the Vegviser API, and the client needs a secure way to obtain and refresh credentials.

Likewise, don't pass an Azure Resource Manager access token to Vegviser: tokens are audience-specific.

## 5. My recommendation for TeamValue

Use this as the target:

- Authentication: Microsoft Entra ID, single tenant.
- Authorization: delegated read access to Vegviser, with group-based restrictions if needed.
- Transport: remote MCP over HTTPS.
- Local Azure operations: the user's existing Azure CLI login, independently of MCP authentication.
- CI: a dedicated workload identity with read-only access to the Vegviser API.
- Governance: Vegviser controls publication and knowledge ownership; the harness retains enforcement.

That gives you one governed knowledge service usable by different agents without coupling it to any one vendor's identity system.

### References

- [Microsoft Learn — Secure an MCP server with Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/agent-id/secure-mcp-server-with-entra-id?utm_source=chatgpt.com)
- [MCP specification — Authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization?utm_source=chatgpt.com)
- [Codex — MCP configuration and authentication](https://learn.chatgpt.com/docs/extend/mcp?utm_source=chatgpt.com)

One question before choosing the exact implementation: when you say AGY, which agent or runtime do you mean? I can then narrow down whether all four clients can use the same native Entra OAuth setup or whether one needs an adapter.
