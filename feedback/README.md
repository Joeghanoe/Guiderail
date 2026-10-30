# Feedback

Draft examples from every repo land here through `~/.golden-path-harness/feedback/` (rule H.1, `/example`). Review them
weekly: move an accepted example into `harness/examples/` with an example number and `verified`, delete the rest, commit.

A human can prepare an accepted draft for submission without changing the active harness checkout:

```bash
python3 -I ~/.golden-path-harness/harness/tools/harness/bundle.py submit-feedback ~/.golden-path-harness/feedback/<draft>.md
```

The command validates the example, creates a local branch and worktree under `~/.golden-path-harness/workspaces/feedback/`,
copies the example into `harness/examples/`, refreshes the index, and stages those two files. Review the staged diff,
then commit, push, and open the PR yourself. It does not contact a remote or create a PR.
