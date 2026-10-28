# Feedback

Draft cases from every repo land here through `~/.harness-feedback/` (rule H.1, `/example`). Review them
weekly: move an accepted case into `harness/cases/` with a case number and `verified`, delete the rest, commit.

A human can prepare an accepted draft for submission without changing the active harness checkout:

```bash
python3 -I ~/.harness/tools/harness/bundle.py submit-feedback ~/.harness-feedback/<draft>.md
```

The command validates the case, creates a local branch and worktree under `~/.harness-feedback-worktrees/`,
copies the case into `harness/cases/`, refreshes the index, and stages those two files. Review the staged diff,
then commit, push, and open the PR yourself. It does not contact a remote or create a PR.
