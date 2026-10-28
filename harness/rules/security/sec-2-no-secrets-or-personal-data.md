---
type: Rule
title: "SEC.2 No secrets or personal data in code, logs, telemetry or prompts"
description: Secrets and personal data stay out of source, logs, telemetry, commit messages, prompts and model context.
rule_id: SEC.2
principle: [/principles/p-07-security-by-design.md, /principles/p-08-observable-by-design.md]
tags: [security, privacy, logging]
applies_to: ["**"]
enforced_by: [hook:guard-read, hook:guard-bash, tool:secret-scan, tool:sonar-read, review]
severity: blocker
status: stable
sources:
  - id: global
    resource: global.instructions.md and security.instructions.md (AI Hub main b0cc2ae)
---

# Rule

- No secret, key, token, password or connection string in code, config, tests, commit messages or docs.
  Reference it (Key Vault, a pipeline variable group); never echo it.
- No personal data in logs or telemetry at any level. Telemetry records counts, sizes, durations and
  types, not names, paths or payloads.
- An agent never reads `.env` files or dumps the environment. Wrapper scripts read secrets themselves
  and pass them on without printing them. Tool secrets live in the user's env file outside any repo
  (`~/.config/harness/.env`); the agent reads `.harness/.env.example` for the variable names and tells the
  user when one is missing or expired (C-016).
- A new telemetry attribute comes with a check that it cannot carry personal data.

# Enforcement

`hooks/guard-read.sh` and `hooks/guard-bash.sh` block reading `.env` and dumping the environment. A
secret scanner in the repo's verify step catches committed secrets. Review checks log and telemetry
statements.

# Boundary

Test data is generated. Real customer data never goes into a test, fixture or local run.
