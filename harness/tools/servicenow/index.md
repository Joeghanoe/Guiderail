# ServiceNow Tools

Read-only access to ServiceNow configuration and metadata tables (rules CLD.1, SEC.2).
Credentials (`SN_INSTANCE`, `SN_USER`, `SN_PASSWORD`) stay in `~/.config/harness/.env` and are never logged or exposed.
Playbook: [analyse-servicenow.md](../../playbooks/analyse-servicenow.md).

## Routing table

| When the user says | Tool / Playbook | Command |
|---|---|---|
| "ServiceNow config" / "why does SN do X?" | Configuration reader | `~/.harness/tools/servicenow/sn-get.sh <table> "<query>" "<fields>"` |
| "check ServiceNow access" / "which tables can we read?" | Access checker | `~/.harness/tools/servicenow/sn-access-check.sh` |
| "analyse ServiceNow" / "business rule or flow issue" | Analysis playbook | `~/.harness/playbooks/analyse-servicenow.md` |

## Allowlisted tables

`sn-get.sh` restricts queries to configuration and metadata tables only (e.g., `sys_script`, `sys_dictionary`, `sys_transform_map`, `sys_update_xml`, `sys_db_object`). It strictly refuses queries against operational or personal data tables (`incident`, `sys_user`, etc.) per rule SEC.2.
