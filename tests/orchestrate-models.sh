echo "== orchestrate models (vendor-neutral)"
# Sourced by tests/run.sh: uses its expect helper and $here, $h, $tmp. Every call pins XDG_CONFIG_HOME to a
# throwaway folder, so a real ~/.config/harness/models.json on the machine running the tests cannot change a result.
om="$h/tools/orchestration/orchestrate.py"
omd="$tmp/orch-models"
mkdir -p "$omd/cfg/harness"

omr() { XDG_CONFIG_HOME="$omd/cfg" python3 -I "$om" "$@"; }
om_has() { # om_has <grep -E pattern> <orchestrate args...>: stdout matches
  local pattern="$1" output
  shift
  output="$(omr "$@" 2>&1)" && grep -Eq -- "$pattern" <<<"$output"
}
om_lacks() { # om_lacks <grep -E pattern> <orchestrate args...>: ran fine and stdout does not match
  local pattern="$1" output
  shift
  output="$(omr "$@" 2>&1)" || return 1
  ! grep -Eq -- "$pattern" <<<"$output"
}
om_json() { # om_json <jq expression> <orchestrate args...>
  local expression="$1" output
  shift
  output="$(omr "$@" 2>&1)" && jq -e "$expression" <<<"$output" >/dev/null
}

today="$(date +%Y-%m-%d)"
cat >"$omd/acme.json" <<J
{"providers": {"acme": {"reviewed": "$today", "economy": "acme-small", "builder": "acme-mid", "reasoner": "acme-large"}}}
J
cat >"$omd/acme-old.json" <<'J'
{"providers": {"acme": {"reviewed": "2020-01-01", "economy": "acme-small", "builder": "acme-mid", "reasoner": "acme-large"}}}
J
echo '{"providers": {"acme": {"economy": "acme-small"}}}' >"$omd/partial.json"
echo '{"providers": {"anthropic": {"reviewed": "2026-01-01", "builder": "user-builder"}}}' >"$omd/user-layer.json"
echo '{not json' >"$omd/malformed.json"
echo '{"providers": {"Bad Name": {"economy": "x"}}}' >"$omd/badname.json"
echo '{"providers": {"acme": {"economy": "x", "turbo": "y"}}}' >"$omd/badtier.json"
printf '{"providers": {"acme": {"economy": "one\\ntwo"}}}\n' >"$omd/control.json"
echo '[]' >"$omd/notobject.json"

SPEC='Build .NET backend with React frontend'

# No provider is the default.
expect 0 "plan with no provider still tiers every work package" om_json '.provider == null and all(.work_packages[]; .tier != null)' plan --spec "$SPEC"
expect 0 "plan with no provider names no model" om_json 'all(.work_packages[]; has("model") | not)' plan --spec "$SPEC"
expect 0 "plan with no provider says how to choose one" om_has 'No provider chosen' plan --spec "$SPEC" --format markdown
expect 0 "markdown plan with no provider has no model column" om_lacks '\| Model \|' plan --spec "$SPEC" --format markdown
expect 0 "tier with no provider lists the configured providers" om_json '(.models | length) >= 1 and (.models_note | length) > 0' tier --task "format and lint files"

# Any vendor works through configuration alone.
expect 0 "a provider added with --models resolves each tier" om_has 'acme-small.*acme-mid.*acme-large|acme-large' plan --spec "$SPEC" --provider acme --models "$omd/acme.json" --format markdown
expect 0 "plan JSON carries the chosen provider and a model per package" om_json '.provider == "acme" and all(.work_packages[]; .model | startswith("acme-"))' plan --spec "$SPEC" --provider acme --models "$omd/acme.json"
expect 0 "tier resolves to the chosen provider only" om_json '(.models | length) == 1 and .models[0].provider == "acme" and .models[0].model == "acme-small"' tier --task "format and lint files" --provider acme --models "$omd/acme.json"
expect 0 "the shipped provider resolves too" om_json 'all(.work_packages[]; .model | startswith("claude-"))' plan --spec "$SPEC" --provider anthropic
expect 0 "HARNESS_MODEL_PROVIDER chooses the provider" bash -c "XDG_CONFIG_HOME='$omd/cfg' HARNESS_MODEL_PROVIDER=acme python3 -I '$om' plan --spec '$SPEC' --models '$omd/acme.json' | jq -e '.provider == \"acme\"' >/dev/null"
expect 0 "--provider wins over the variable" bash -c "XDG_CONFIG_HOME='$omd/cfg' HARNESS_MODEL_PROVIDER=nope python3 -I '$om' plan --spec '$SPEC' --provider acme --models '$omd/acme.json' | jq -e '.provider == \"acme\"' >/dev/null"

# A name is never guessed.
expect 1 "a provider that is not configured is an error" omr plan --spec "$SPEC" --provider nope
expect 0 "the error names what is configured" bash -c "XDG_CONFIG_HOME='$omd/cfg' python3 -I '$om' plan --spec '$SPEC' --provider nope 2>&1 | grep -q 'configured: anthropic'"
expect 0 "a partial entry gives no name for a missing tier, not another vendor's" om_json '[.work_packages[] | select(.tier != "economy")] | all(.model == null)' plan --spec "$SPEC" --provider acme --models "$omd/partial.json"

# Layers: shipped, then the user's, then --models; a later layer replaces a provider whole.
cp "$omd/user-layer.json" "$omd/cfg/harness/models.json"
expect 0 "the user's file replaces the shipped provider whole" om_json '[.work_packages[] | select(.tier == "builder")][0].model == "user-builder" and ([.work_packages[] | select(.tier == "reasoner")][0].model == null)' plan --spec "$SPEC" --provider anthropic
expect 0 "--models replaces the user's file for the same provider" om_json '[.work_packages[] | select(.tier == "builder")][0].model == "acme-mid"' plan --spec "$SPEC" --provider acme --models "$omd/acme.json"
rm -f "$omd/cfg/harness/models.json"

# Names rot: an old date is flagged, a recent one is not.
expect 0 "an old reviewed date is flagged" om_has 'last checked: 2020-01-01' plan --spec "$SPEC" --provider acme --models "$omd/acme-old.json" --format markdown
expect 0 "a recent reviewed date is not flagged" om_lacks 'last checked' plan --spec "$SPEC" --provider acme --models "$omd/acme.json" --format markdown
expect 0 "a missing reviewed date is flagged" om_has 'no date recorded' plan --spec "$SPEC" --provider acme --models "$omd/partial.json" --format markdown

# Bad configuration fails loudly instead of being skipped.
expect 1 "malformed JSON is an error" omr tier --task x --models "$omd/malformed.json"
expect 1 "a provider name with a space is an error" omr tier --task x --models "$omd/badname.json"
expect 1 "an unknown tier key is an error" omr tier --task x --models "$omd/badtier.json"
expect 1 "a control character in a name is an error" omr tier --task x --models "$omd/control.json"
expect 1 "a top-level array is an error" omr tier --task x --models "$omd/notobject.json"
expect 1 "a missing --models file is an error" omr tier --task x --models "$omd/does-not-exist.json"

# The thing this file exists to protect: no vendor's model name outside the one config file.
expect 1 "no vendor model name in the tool's code" grep -Eqi 'claude-[a-z]|gpt-[0-9]|gemini-[0-9]|\bo[13]\b' "$om"
expect 1 "no vendor model name in the playbook" grep -Eqi 'claude-[a-z]|gpt-[0-9]|gemini-[0-9]' "$h/playbooks/orchestrate-workload.md"
expect 1 "no vendor model name in the tool index" grep -Eqi 'claude-[a-z]|gpt-[0-9]|gemini-[0-9]' "$h/tools/orchestration/index.md"
