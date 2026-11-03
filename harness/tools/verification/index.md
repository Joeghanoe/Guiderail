# Verification contracts and evidence

`requirements.json` is a versioned registry of scoped requirements, their methods, available tools and residual judgment. It travels with the bundle under tools, outside OKF concept discovery. Existing concept types, rule IDs, verdicts and routing remain compatible.

```bash
python3 -I harness/tools/verification/verify.py check
```

A tool's presence means available implementation. It does not establish installation or required execution in a consumer. The registry retains implemented, standard-tool-candidate, custom-automation-candidate, hybrid, semantic-only and guidance-only states. Methods remain independent. An `automation-candidate` example can link to an implemented tool without changing its verdict.

## Record a command

Run from a Git repository root. Choose a new directory outside both the source repository and the harness.

```bash
python3 -I .harness/tools/verification/verify.py run \
  --requirement T.1.verify-command --repo . --stage local \
  --out /tmp/orders-verification/command --timeout 1800 \
  -- bash scripts/verify.sh
```

This records command completion and retained output, not proof that the command implements every convention. Generic commands cannot claim a structural or semantic requirement passed. Source changes during verification produce an error.

## Check C# changes independently of retrieval

```bash
python3 -I .harness/tools/verification/verify.py code-types \
  --repo . --baseline origin/main --symbols none --symbols DEBUG \
  --out /tmp/orders-verification/code-types
```

Use the PR merge-base commit for CI. Local default is HEAD and includes uncommitted/untracked changes. No baseline commit in a newly initialized repository means every declaration is new. Supported configurations belong to the adopting repository; the runner does not guess them. A conditional source without explicit symbols produces an error. `--audit` is an explicit full-tree alternative.

The runner copies/builds the existing SDK-backed checker in temporary storage and preserves its schema 2 output. It reports actionable introduced findings and retains inherited ones separately. Exit 0 passes the checked scope, exit 1 reports findings, exit 2 reports errors. A no-change run is explicitly not-applicable. The generated-marker and private-helper limits remain documented in the CODE.5 gate.

## Summarize required evidence

```bash
python3 -I .harness/tools/verification/verify.py report \
  --out /tmp/orders-verification/receipt.json \
  --required T.1.verify-command CODE.5.file-layout \
  --review CODE.5.responsibility \
  --results /tmp/orders-verification/command/receipt.json \
  /tmp/orders-verification/code-types/receipt.json
```

The caller explicitly names required checks independently of selection. Missing, errored, skipped, waived or inconclusive required results leave verification incomplete. Waivers need a separate authority decision; this command does not approve them. Receipts from different source/harness/registry states or duplicate attempts are rejected. Select the final attempt explicitly. A pass says checks-passed, never approved. Semantic requirements remain pending and link to separate review.

Receipts distinguish source revision/dirty state, stage, exact argv, timeout, exit status, evidence hashes, coverage and approval state. Untracked state is fingerprinted using metadata to avoid reading arbitrary env/credential files. It is not a cryptographic attestation of all untracked content. Logs can contain sensitive output from the consumer command; keep them in access-controlled temporary storage or CI artifacts and use the consumer's established redaction policy. No automatic remediation executes arbitrary finding text.

## Review and retrieval

`review.sh` supplies `semantic-plan.json` with applicable registry scopes and rubric references to the separate reviewer. Findings keep existing public rule IDs and JSON shape. The registry does not create an automatic numeric semantic gate. Calibrate the rubric before making scores blocking; human review remains authoritative.

Claude and agy edit hooks call `tools/harness/context.py`. A successful lookup plus document hashes produces a temporary session receipt before edit guidance is cached. Newly relevant content is delivered even for an already-seen extension. Failed selection blocks the edit and writes no success marker. Without a session ID, context is delivered uncached. A selection receipt records references, not a claim that the agent opened the documents.

## Adoption and maintenance

The full verify template runs CODE.5 locally. The reusable PR pipeline runs CODE.5 once as an independent step, records the configured verify command, summarizes results and publishes failure evidence. `HARNESS_CODE5_EXTERNAL=1` avoids a duplicate run inside the updated template. Required branch policies and consumer adoption still belong to the repository owner. Other analyzers and scenario mappings retain their existing opt-in status.

Gitleaks scanning and the selected PSRule Key Vault profile now have pinned adapters and real-engine fixtures. Installation is explicit through `install-tools.py`. Keep audit and calibration reports under `$GOLDEN_PATH_HOME/testing/`, outside the source checkout. Existing reviewer scenarios and task benchmarks remain the outcome evaluators; no performance improvement is asserted without running the experiment.

## Install pinned scanners

PowerShell must already be available for the Key Vault pilot. Install the locked tools into a local cache, then run checks without downloading dependencies:

```bash
tools_dir="${GOLDEN_PATH_HOME:-$HOME/.golden-path-harness}/cache/verification-tools"
testing_root="${GOLDEN_PATH_HOME:-$HOME/.golden-path-harness}/testing"
mkdir -p "$testing_root/runs"
run_dir="$(mktemp -d "$testing_root/runs/verification.XXXXXX")"
python3 -I .harness/tools/verification/install-tools.py --out "$tools_dir"
python3 -I .harness/tools/verification/verify.py gitleaks \
  --repo . --tools "$tools_dir" --working-tree --out "$run_dir/secrets"
python3 -I .harness/tools/verification/verify.py psrule \
  --repo . --tools "$tools_dir" --template infra/vault.bicep \
  --parameters infra/vault.dev.parameters.json --out "$run_dir/vault"
```

Use a fresh output directory for each invocation. `tool-lock.json` pins versions, download hashes and the adopted Key Vault rules. The pilot accepts Bicep or ARM templates with optional ARM deployment-parameter JSON. Repository owners choose whether these checks are required. Secret scanning covers recognizable patterns, and Key Vault results cover only the supplied deployment inputs. Retain run evidence in local testing storage or CI artifacts rather than committing it.
