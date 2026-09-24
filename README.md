# Autonomous Database Health Assistant

Read-only database operations assistant for Oracle Private Agent Factory 26.7.

The implementation is delivered in three phases:

1. **Database backend:** dedicated accounts, five monitoring functions, SQLcl deployment and live permission tests.
2. **Agent Builder:** configure a private model, database data source, approved PL/SQL tools and chat flow.
3. **Pilot validation:** exercise realistic DBA questions, failure handling, private network/data flow and restricted sharing.

The database connection is `DB_HEALTH_AGENT`. `DB_HEALTH_OWNER` owns the
definer-rights package and cannot log in. ADMIN is used only to provision and
deploy into the owner schema. No objects are installed into ADMIN or SYS.

```text
Agent Factory -> DB_HEALTH_AGENT.DB_HEALTH_API -> DB_HEALTH_OWNER.DB_HEALTH_API
                                      -> five approved Oracle monitoring views
```


## Select AI monitoring LiveLab

For the newer conversational Agent using Select AI Bridge, follow the
[step-by-step monitoring LiveLab](docs/livelab/README.md). It includes database
preparation, UI configuration, the final Agent prompt and validation exercises.
This is a separate flow from the original fixed PL/SQL API walkthrough below.
For a prepared database, use the [PAF configuration-only alternative](docs/livelab-paf-only/README.md).

## Phase 1: database backend

All database operations use the SQLcl bundled with the Oracle SQL Developer
extension, as configured in `scripts/db.py`. The helper requires a saved SQLcl
connection and the exact database identity; it stops on an unexpected database
or login. Python uses only its standard library.

Run from this repository, substituting your existing connection and the exact
value returned by `SYS_CONTEXT('USERENV','DB_NAME')`:

```bash
python3 scripts/db.py preflight --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py provision --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py install --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py verify-admin --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
```

Provisioning creates a 40-character random password at
`.local/db_health_agent.password` (directory mode 0700; file mode 0600).
It is passed to SQLcl over stdin with history/echo disabled and is never placed
in command-line arguments. `.local/` is ignored by Git. Treat the file as a
credential and enter its contents only in a password field or approved secret store.
Do not paste it into chat or commit it. The owner has `NO AUTHENTICATION`.

Provisioning refuses to adopt existing users or overwrite a credential file.
DDL commits independently: on failure, inspect the created users and grants
before resuming. Do not delete the password file merely to force a retry. Package
installation is repeatable; no automatic schema-drop or password-reset operation
is supplied. The scripts are deliberately tied to the approved account names.

After provisioning, clone the admin connection's network configuration in SQLcl
with the runtime username and **without** the saved admin password:

```sql
connmgr clone -original "YOUR_ADMIN_CONNECTION" -username DB_HEALTH_AGENT -nopwd "YOUR_RUNTIME_CONNECTION"
```

Then verify through an actual runtime login:

```bash
python3 scripts/db.py verify-runtime --connection 'YOUR_RUNTIME_CONNECTION' --expected-db YOUR_DB_NAME
```

This runtime connection must have no saved password: the helper supplies the
generated password over SQLcl stdin with command history disabled. It is a local SQLcl connection;
it does not create an Agent Factory data source.

## Monitoring interface

Agent-facing routines are in `DB_HEALTH_AGENT.DB_HEALTH_API`. They delegate to
`DB_HEALTH_OWNER.DB_HEALTH_API`, return a JSON CLOB and
accepts no SQL text, database name or object name from the caller.

| Function | Parameters | Evidence |
| --- | --- | --- |
| `GET_DATABASE_OVERVIEW` | None | Reachability, caller identity, service and database/container identity |
| `GET_SESSIONS` | `P_LIMIT` default 20 | Active/blocked user sessions, waits and blocking session/instance IDs |
| `GET_STORAGE_USAGE` | `P_LIMIT` default 20 | Tablespace used bytes, capacity bytes and percentage |
| `GET_FAILED_JOBS` | `P_HOURS_BACK` default 24; `P_LIMIT` default 20 | Failed Scheduler runs, timestamps and numeric error codes |
| `GET_SQL_WORKLOAD` | `P_LIMIT` default 20 | Cached per-instance SQL statistics ranked by cumulative elapsed time |

Limits must be integers from 1 to 100. History must be an integer from 1 to 168
hours. Explicit nulls and out-of-range values return `invalid_input`. These are
bounded responses, not query-duration limits; configure a supported execution
timeout in the Agent Factory/runtime environment before a production pilot.

Responses contain `api_version`, `check`, `status`, `database`, `container`,
`collected_at_utc`, `source`, `row_count`, `truncated`, `rows` and `note`.
Failures include `error_code` and a generic `message`. No raw SQL, SQL bind values,
job action text, or free-form Scheduler error output is included.

- `ok` means collection succeeded, **not** overall database health.
- `unavailable` means the executing function failed; it returns no partial rows.
- Connection failures and invalid-package errors can occur before a function
  executes. The Agent Builder prompt must treat tool-level errors the same way.
- An empty failure-history result means no retained matching records; it does
  not prove every expected job ran.
- SQL statistics are cumulative cache counters, not historical windows. Parallel
  execution and repeated executions affect totals and averages.
- Tablespace capacity includes Oracle's autoextend calculations and is distinct
  from Autonomous service provisioned storage or OCI `StorageUtilization`.
- Visibility is the connected Autonomous container, not the underlying fleet.

## Phase 2 and 3

Use [the Agent Builder setup guide](docs/agent-builder.md) and
[agent instructions](agent/system-prompt.txt). Database deployment does not
configure or publish the agent. Private endpoint routing, private LLM hosting,
tool-result serialization in Agent Factory and tracing destinations must be
verified in the application environment.

The live SQL tests cover account grants, package validity, real runtime login,
all five responses, bounds, invalid inputs, truncation when data is available,
metadata discovery and denied direct monitoring-view access. They do not create
blocking sessions or intentionally fail Scheduler jobs on the target database.
Those controlled fixtures and simulated tool failures belong in the pilot test
environment. A successful SQLcl test is not an end-to-end Agent Factory test.

## References

- [Oracle Agent Builder components, 26.7](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html)
- [Agent Factory database data sources](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html)
- [Schema-only accounts](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/CREATE-USER.html)
- [Definer-rights procedure privileges](https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/how-procedure-privileges-affect-definers-rights.html)

## Same-schema discovery compatibility

The installed Agent Factory UI listed the overview function only after a wrapper
was created in DB_HEALTH_AGENT (confirmed by the user on 2026-09-24). The normal
install now deploys all five same-schema wrappers via `db/05_runtime_api.sql`.
They delegate to the original owner package and need no extra privileges.
`verify-runtime` now exercises this agent-facing path. On an existing installation,
run the `install-runtime-api` action with the ADMIN connection and expected database,
then run `verify-runtime`. Refresh the Agent Factory node and select the five
DB_HEALTH_AGENT routines. End-to-end tool execution remains to be checked in the UI.
