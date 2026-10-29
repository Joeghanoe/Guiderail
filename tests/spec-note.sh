echo "== spec-note"
spec="$h/tools/spec/spec-note.py"
note() { python3 -I "$spec" "$@"; }                 # with HARNESS_VAULT unset by the caller
vault="$tmp/vault"
mkdir -p "$vault/contoso" "$tmp/outside"
unset HARNESS_VAULT

expect 2 "spec-note needs a subcommand" note --customer contoso
expect 1 "no vault, no write" note new --customer contoso --title "Partner order sync"
expect 1 "a vault path that is not a folder is refused" note new --vault "$vault/nope" --customer contoso --title "Partner order sync"
expect 1 "a customer folder that is not in the vault is refused" note new --vault "$vault" --customer absent --title "Partner order sync"
expect 0 "new writes <vault>/<customer>/specs/<slug>.md" note new --vault "$vault" --customer contoso --title "Partner order sync" --work-item AB-12 --owner human:ab --source-note "AB-12 Analysis" --tag orders
expect 0 "the note is at the slug of its title" test -f "$vault/contoso/specs/partner-order-sync.md"
expect 0 "front matter carries title, spec id, work item, tags and the wikilink" bash -c "grep -q 'title: \"Partner order sync\"' '$vault/contoso/specs/partner-order-sync.md' && grep -q 'spec_id: partner-order-sync' '$vault/contoso/specs/partner-order-sync.md' && grep -q 'work_item: AB-12' '$vault/contoso/specs/partner-order-sync.md' && grep -q 'tags: \[spec, orders\]' '$vault/contoso/specs/partner-order-sync.md' && grep -q '\- \"\[\[AB-12 Analysis\]\]\"' '$vault/contoso/specs/partner-order-sync.md'"
expect 0 "the acceptance criteria name T.5 and DEL.3" bash -c "grep -q 'T.5' '$vault/contoso/specs/partner-order-sync.md' && grep -q 'DEL.3' '$vault/contoso/specs/partner-order-sync.md'"
expect 0 "a spec without a work item or a source note is still written" note new --vault "$vault" --customer contoso --title "Invoice retry"
expect 0 "the placeholders it did not fill stay visible" grep -q "{{work_item}}" "$vault/contoso/specs/invoice-retry.md"
expect 0 "without a source note the wikilink is commented out, not an empty link" bash -c "grep -q '# - \"\[\[{{source_note}}\]\]\"' '$vault/contoso/specs/invoice-retry.md'"

echo "x" >>"$vault/contoso/specs/partner-order-sync.md"
expect 2 "new refuses to overwrite an existing spec" note new --vault "$vault" --customer contoso --title "Partner order sync"
expect 0 "the refused run changed nothing" bash -c "tail -1 '$vault/contoso/specs/partner-order-sync.md' | grep -qx x"
expect 0 "--force replaces it" note new --vault "$vault" --customer contoso --title "Partner order sync" --force
expect 1 "--force did replace it" bash -c "tail -1 '$vault/contoso/specs/partner-order-sync.md' | grep -qx x"

expect 1 "a customer folder of .. is refused" note new --vault "$vault" --customer ".." --title "Partner order sync"
expect 1 "a customer path instead of a folder name is refused" note new --vault "$vault" --customer "contoso/specs" --title "Partner order sync"
expect 1 "an absolute customer folder is refused" note new --vault "$vault" --customer "$tmp/outside" --title "Partner order sync"
expect 1 "a hidden customer folder is refused" note new --vault "$vault" --customer ".git" --title "Partner order sync"
expect 1 "a slug that traverses is refused" note new --vault "$vault" --customer contoso --title "Partner order sync" --slug "../../escape"
expect 1 "a title with no slug characters is refused" note new --vault "$vault" --customer contoso --title "???"
ln -sfn "$tmp/outside" "$vault/linked"
expect 1 "a symlinked customer folder that leaves the vault is refused" note new --vault "$vault" --customer linked --title "Partner order sync"
mkdir -p "$vault/beta" && ln -sfn "$tmp/outside" "$vault/beta/specs"
expect 1 "a symlinked specs folder that leaves the vault is refused" note new --vault "$vault" --customer beta --title "Partner order sync"
expect 0 "nothing was written outside the vault" bash -c "test -z \"\$(ls -A '$tmp/outside')\""

expect 0 "HARNESS_VAULT is used when --vault is absent" bash -c "HARNESS_VAULT='$vault' python3 -I '$spec' list --customer contoso | grep -q partner-order-sync.md"
expect 0 "set changes a front-matter value it finds" note set --vault "$vault" --customer contoso --slug partner-order-sync --field status=agreed
expect 0 "status is agreed and the comment survives" bash -c "grep -q 'status: agreed .*# draft | agreed' '$vault/contoso/specs/partner-order-sync.md'"
expect 1 "set does not add a key the note lacks" note set --vault "$vault" --customer contoso --slug partner-order-sync --field bogus=1
expect 0 "the refused set changed nothing" grep -q "status: agreed" "$vault/contoso/specs/partner-order-sync.md"
expect 1 "set refuses a field that is not key=value" note set --vault "$vault" --customer contoso --slug partner-order-sync --field status
expect 1 "set needs an existing spec" note set --vault "$vault" --customer contoso --slug absent --field status=agreed
mkdir -p "$vault/gamma"
expect 0 "list is quiet for a folder without specs" bash -c "test -z \"\$(python3 -I '$spec' list --vault '$vault' --customer gamma)\""
expect 0 "list shows both specs of the folder" bash -c "python3 -I '$spec' list --vault '$vault' --customer contoso | wc -l | grep -q 2"
