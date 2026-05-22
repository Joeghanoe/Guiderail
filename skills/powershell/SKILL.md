---
name: powershell
description: "Write PowerShell scripts and functions following enterprise conventions. Use when: writing new PowerShell functions, creating Azure automation scripts, refactoring .ps1 files, designing parameters, implementing error handling, building retry logic, writing idempotent deployment scripts, allcreating PowerShell modules."
---

# PowerShell Code Writing

## When to Use

- Writing new PowerShell functions or scripts
- Creating Azure resource automation scripts which cannot be done in Bicep
- Refactoring or reviewing existing `.ps1` / `.psm1` files
- Designing parameter blocks with proper validation

## Rules

### Function Structure

- Every function MUST use `[CmdletBinding()]`
- Declare `[OutputType()]` when the return type is deterministic
- Include comment-based help: `.SYNOPSIS` and `.DESCRIPTION` are required; add `.OUTPUTS`, `.NOTES`, `.EXAMPLE` when the function behavior is non-obvious
- Use `#Requires` statements at script level for PowerShell version and module dependencies
- Use approved PowerShell verbs (`Get-`, `Set-`, `New-`, `Remove-`, `Update-`, `Invoke-`, `Test-`, `Add-`) — run `Get-Verb` if unsure

### Parameter Design

- Type every parameter explicitly: `[string]`, `[int]`, `[bool]`, `[hashtable]`, `[switch]`, `[string[]]`
- Mark required parameters with `[Parameter(Mandatory = $true)]`; provide sensible defaults for optional ones
- Use validation attributes to constrain input:
  - `[ValidateSet()]` for fixed option lists
  - `[ValidatePattern()]` for structured strings (resource names, versions)
  - `[ValidateNotNullOrEmpty()]` for required strings that must have content
  - `[ValidateRange()]` for bounded numeric values
- Order parameters logically: identity/target first, configuration second, feature toggles and switches last
- For comma-separated list inputs, accept `[string]` and split internally rather than forcing the caller to provide arrays

### Output Stream Discipline

| Stream              | Use For                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| `Write-Information` | Progress and tracing messages for operators. Default for logging statements. |
| `Write-Error`       | Terminal failures that should halt execution                                 |
| `Write-Warning`     | Non-fatal anomalies worth noting                                             |
| `Write-Verbose`     | Detailed debugging (gated behind `-Verbose`)                                 |
| `Write-Output`      | Return values ONLY — never mix with status text                              |

- NEVER use `Write-Host` — it bypasses the output stream system and is untestable
- Do not return values via `Write-Information`; use `Write-Output` or implicit output

### Error Handling

- Set `$ErrorActionPreference = 'Stop'` at the top of scripts for fail-fast behavior
- Use `-ErrorAction SilentlyContinue` only for existence-check lookups (e.g., "does this resource exist?")
- Implement retry logic with a configurable timeout and progressive back-off for operations prone to transient failures
- Use `try/finally` when cleanup is required regardless of success (restoring state, releasing locks)
- Use `throw` for unrecoverable precondition violations; use `Write-Error` for reportable operational failures
- Never swallow errors with empty `catch {}` blocks

### Idempotency & Guard Clauses

- Before creating or modifying a resource, check whether the desired state already exists
- Return early when the current state matches the target — do not re-apply changes unnecessarily
- Log the decision path clearly: "Resource X already exists, skipping creation" vs "Resource X not found, creating"
- In orchestration scripts, use numbered step comments (e.g., `# 1. Validate inputs`, `# 2. Create subnet`) for auditability

### Script-Level Conventions

- Declare a full `param()` block at the top with typed, validated parameters
- Set preference variables immediately after the param block:
  - `$ErrorActionPreference = 'Stop'`
  - `$InformationPreference = 'Continue'`
- Validate all preconditions (naming conventions, resource existence, compatibility) before any mutation
- Derive resource names from conventions and parameters — never require the caller to compute dependent names
- End orchestration scripts with a cleanup/rollback section if temporary resources were created

### Naming & Composition

- Name functions using the `Verb-Noun` pattern with a domain-specific noun (e.g., `Get-SubnetConfiguration`, `Update-PrivateEndpoints`)
- Group related functions in domain-specific `.ps1` files and compose modules via dot-sourcing
- Use splatting (`@params`) for cmdlet calls with more than three parameters
- Return complex results as hashtables or `[PSCustomObject]` rather than multiple output statements
- Keep helper functions scoped to their domain file; do not pollute the global namespace

### Azure Resource Scripting

- Use `-ErrorAction SilentlyContinue` when checking if a resource exists before acting
- Parse resource group names for environment/region/team when they follow a naming convention
- Validate input parameters against known constraints (e.g., allowed SKUs, regions, naming rules) before calling Azure APIs
- When deploying ARM/Bicep templates, generate deployment names that include a timestamp and are capped at 64 characters
- For web/API calls, always include `-UseBasicParsing` and set proper `Content-Type` and `Authorization` headers via splatting

### Security

- Never hardcode secrets, connection strings, or tokens in script bodies
- Acquire tokens through module-provided mechanisms (e.g., `Get-AzAccessToken -AsSecureString`)
- When converting SecureString to plain text for API calls, zero the intermediate buffer in a `finally` block
- Avoid `Invoke-Expression` — use splatting or `& $command @args` for dynamic invocation
- Validate and sanitize inputs before constructing URIs, resource paths, or queries to prevent injection

## Anti-Patterns to Reject

1. `Write-Host` for anything other than interactive-only console formatting
2. Untyped parameters without any validation
3. Empty `catch {}` blocks that hide failures
4. `Invoke-Expression` for constructing dynamic commands
5. Mixing `Write-Output` return values with status messages in the same function
6. Polling loops (`Start-Sleep`) without a timeout boundary
7. Hardcoded resource names, IPs, or secrets
8. Functions missing `[CmdletBinding()]`
9. Returning `$null` silently when an error occurred — always signal failure via the error stream
10. Over-engineering: adding parameters, validation, or abstraction for scenarios that will never occur
