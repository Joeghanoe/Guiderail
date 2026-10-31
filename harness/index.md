---
okf_version: "0.2"
---

# TeamValue harness

Start here. Open only the folder and the files your task touches.

Source: [Way of Work](https://teamvaluebv.sharepoint.com/:fl:/g/contentstorage/CSP_88230063-5b4c-4bd7-9a8a-8bf8738fdb0d/IQBY32cKRPtmSJsbqc88e9n1AcmAdL8k0YLgclNAAf39FPE?e=K9KPQp&nav=cz0lMkZjb250ZW50c3RvcmFnZSUyRkNTUF84ODIzMDA2My01YjRjLTRiZDctOWE4YS04YmY4NzM4ZmRiMGQmZD1iJTIxWXdBamlFeGIxMHVhaW92NGM0X2JEUjQ0SmRrUnJBWkp1UmhaOFBHYjdxZjVTUllIRmJhdFQ1ZTlUUlk5NUxIRCZmPTAxMkNENE5CMlkzNVRRVVJIM01aRUpXRzVKWjQ2SFhXUFYmYz0lMkYmYT1Mb29wQXBwJnA9JTQwZmx1aWR4JTJGbG9vcC1wYWdlLWNvbnRhaW5lcg%3D%3D)

* [Principles](principles/) - P1-P13, pointers to Vegviser, which is the authority
* [Rules](rules/) - what follows from them, with the tool or hook that enforces each one
* [Examples](examples/) - worked examples with a verdict; human-reviewed examples are precedent
* [Playbooks](playbooks/) - review a change, add an example, orchestrate a workload, process feedback, classify a test failure, write a business test plan, analyse ServiceNow, draw an integration diagram, verify a deployment, triage an incident
* [Gates](gates/) - registration of each deterministic check: tool, owner, coverage, blind spots

# Tools

* [tools/](tools/) - scripts grouped by domain, see its index: harness, review, testing, cloud, azure-devops, servicenow, sonar, diagrams, orchestration
* [hooks/](hooks/) - Claude Code guard hooks: bash, read, stop-verify
* [templates/](templates/) - `example.md` for feedback, `finding.md` for a review finding, `business-testplan.spec.json` for a business test plan, `solution-design.md` for a new service's design, `repo/` for what a project repo owns (AGENTS.md, verify.sh, analyzers)
