# Rules

* [CLD.1 Agents only read cloud state](cld-1-agents-read-cloud-state.md) - Agents use cloud CLIs and APIs read-only, through the wrapper, with a read-only identity.
* [CLD.2 Irreversible or outward actions are taken by a human](cld-2-humans-take-irreversible-actions.md) - Deploy, apply, push to a default or release branch, merge, run a pipeline, grant access, change retention or send a message only on a human go-ahead; an agent may push a named feature branch.
