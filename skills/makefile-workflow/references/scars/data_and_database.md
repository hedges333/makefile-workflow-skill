# Data and Database Protection Scars

This reference manual documents database safety, data isolation, and query scars (`SCAR-DATA-*` and `SCAR-DB-*`).

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-DB-09` | Pipeline Splitting and URI Userinfo Stripping | Database Tool Guard Parsing |

---

### SCAR-DB-09: Pipeline Splitting and URI Userinfo Stripping

- **Wound**: Production database guard hooks fail to block dangerous commands in piped shell commands (such as `echo "sql" | psql production_db`) or trigger false alarms on database passwords embedded in connection URIs.
- **Trap**: Checking only the primary command name and failing to tokenize pipeline stages or parse connection string URIs.
- **Permanent Reflex**: Split compound shell pipelines into individual command segments and strip URI userinfo credentials before evaluating database safety tokens.
