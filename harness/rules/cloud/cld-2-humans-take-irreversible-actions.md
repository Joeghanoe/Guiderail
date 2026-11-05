---
type: Rule
title: "CLD.2 Irreversible or outward actions are taken by a human"
description: Deploy, apply, push to a default or release branch, merge, run a pipeline, grant access, change retention or send a message only on a human go-ahead; an agent may push a named feature branch.
rule_id: CLD.2
principle: /principles/p-03-governed-autonomy.md
tags: [safety, delivery]
applies_to: ["**"]
enforced_by: [hook:guard-bash, instructions]
severity: blocker
status: stable
sources:
  - id: security
    resource: security.instructions.md (AI Hub main b0cc2ae), OWASP LLM06
  - id: vegviser
    resource: TeamValue.Vegviser PR #300, 40-consulting-capabilities/Governed SDLC Engineering Standards.md v1.1 (CLD.2)
---

# Rule

An agent proposes these and stops; a human performs them:

- `terraform apply`, `terraform plan` against a real backend, a Bicep or ARM deployment
- a push to the default branch (`main`, `master`, or what `origin/HEAD` points to) or a release branch (`release/*`); a force push; deleting or rewriting a shared branch; pushing tags
- merging a PR, approving a PR
- running or approving a pipeline, changing a pipeline variable or service connection
- granting or widening access, in any tenant
- enabling WORM, setting or extending retention, changing lifecycle rules
- sending anything outside the session: mail, chat, tickets, PR comments in someone else's name

An agent may push a feature branch, named on the command line: `git push -u origin <feature-branch>`. That makes the change available for the pipeline and review; branch protection on the default and release branches is the real boundary, the hook is a guardrail on top of it. A push counts as a deployment, and stays with a human, when the branch's pipeline does more than build, test and review (for example it deploys feature branches to a shared environment).

Approval in one context does not extend to the next.

# Segregation of Duties and Roles

When proposing deployments or reviews, respect the Way-of-Work role separation:

- **Pull Requests**: The Developer cannot be the Reviewer (Segregation of Duties). A Required Reviewers policy must include an architect or lead developer.
- **Deployments (DTAP)**:
  - **DEV**: Automated after CI, owned by the Developer.
  - **TST**: Requires explicit approval, preferably by the **Tester**.
  - **ACC**: Requires explicit approval, preferably by the **Application Manager**.
  - **PRD**: Requires explicit approval strictly by the **Product Owner** (PO) or delegate ("One Button Deploy"). Members of the BizDevOps team never approve production deployments (exception: critical emergency hotfixes, which must be peer-reviewed post-deployment).

# Enforcement

[guard-bash.sh](../../hooks/guard-bash.sh) lets a push through only when it names a feature branch; it blocks a push to the default or a release branch, a push without a named target, force pushes, deletions, tags and `--all`. It also blocks `gh pr merge`, `gh workflow run`, `az pipelines run` and the cloud CLIs. The rest relies on the identity ([CLD.1](cld-1-agents-read-cloud-state.md)), branch protection and this rule.

# Related guidance

This rule applies [P3 Governed Autonomy](../../principles/p-03-governed-autonomy.md).
