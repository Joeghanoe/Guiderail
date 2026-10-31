# Rules

* [DEL.1 Roll forward, never roll back](del-1-roll-forward.md) - A broken release is fixed by a new release, not by redeploying an older one.
* [DEL.2 Frameworks at n-1](del-2-frameworks-n-minus-1.md) - Use the current stable framework version or the one before it, never older.
* [DEL.3 A change shows its evidence and solves one problem](del-3-a-change-shows-its-evidence-and-does-one-thing.md) - A PR says how the change was checked and what was not, fixes one underlying problem, and names who approved a change of direction.
* [DEL.4 A new repo or service starts with its design, written before the code](del-4-a-new-service-starts-with-its-design.md) - A solution design, an ADR for each decision that is hard to reverse, the repo's own AGENTS.md and a verify command exist before the first feature code, and the code follows them.
