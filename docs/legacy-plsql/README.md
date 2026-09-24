# Legacy PL/SQL Database Health Assistant


This README describes the earlier fixed PL/SQL API implementation. For the current Select AI Bridge flow and workshops, return to the [main README](../../README.md).

## Accounts and architecture

`DB_HEALTH_AGENT` is the runtime login. `DB_HEALTH_OWNER` is a schema-only account with `NO AUTHENTICATION`; it owns the definer-rights monitoring package and cannot log in. ADMIN provisions the accounts and deploys the packages. The runtime package exposes same-schema wrappers for PAF routine discovery.

The Select AI Bridge flow does not use this package path or require the owner schema for its queries. Existing legacy objects can remain in place without participating in that flow.

This implementation remains available for workflows using Oracle PL/SQL Executor:

```text
Agent → Oracle PL/SQL Executor → DB_HEALTH_AGENT.DB_HEALTH_API
                             → DB_HEALTH_OWNER.DB_HEALTH_API
                             → approved monitoring sources
```

## Monitoring interface

| Function | Parameters | Evidence |
|---|---|---|
| `GET_DATABASE_OVERVIEW` | None | Identity and reachability |
| `GET_SESSIONS` | `P_LIMIT`, default 20 | Active/blocked sessions |
| `GET_STORAGE_USAGE` | `P_LIMIT`, default 20 | Tablespace usage |
| `GET_FAILED_JOBS` | `P_HOURS_BACK`, default 24; `P_LIMIT`, default 20 | Retained failed Scheduler runs |
| `GET_SQL_WORKLOAD` | `P_LIMIT`, default 20 | Cumulative cached SQL |

These functions return JSON CLOBs, accept no SQL text or object names, and validate integer row limits of 1–100 and job-history windows of 1–168 hours. Those parameter bounds and JSON response contracts belong to the fixed API; they are not inherently imposed by Select AI Bridge. Do not add a generic SQL execution routine or write operation to `DB_HEALTH_API`.

The same-schema runtime package delegates to the non-login owner's package so PAF can discover the routines. Package installation uses `db/02_package_spec.sql`, `db/03_package_body.sql`, `db/04_validate_install.sql` and `db/05_runtime_api.sql` through `scripts/db.py`. The [earlier Agent Builder guide](../agent-builder.md) and [PL/SQL Agent prompt](../../agent/system-prompt.txt) apply to that flow, not the current Bridge flow. Its historical integration results are in the [instructions-updated report](../../tests/paf/results-instructions-updated-2026-09-24.md).

## Verification boundaries

**Legacy verification is specific to the package-only privilege model.** `db/tests/admin.sql` expects exactly one runtime object grant, and `db/tests/runtime.sql` expects direct monitoring-view reads to be denied. Accordingly, `scripts/db.py verify-admin` and `verify-runtime` are not acceptance checks for the current Select AI-enabled account. Its additional authorized grants conflict with those assertions. Use the current view-verification script and Agent regression for the Select AI path; do not revoke required grants just to satisfy legacy tests.

## Provisioning and tooling

The project helper `scripts/db.py` handles the original account/package setup using a saved connection and expected database identity. Provisioning creates a random password in `.local/db_health_agent.password` with restricted permissions and refuses to adopt existing users or overwrite that file. It supplies the password over SQLcl stdin rather than command-line arguments. DDL may commit before a later failure; inspect partial state instead of rerunning or resetting credentials blindly.

The helper's provisioning operation creates both the runtime and schema-only owner accounts; it is not a Select AI-only provisioning operation. Package installation and discovery details are documented in the [earlier Agent Builder guide](../agent-builder.md) and [same-schema compatibility notes](../same-schema-discovery-test.md).

Use the SQLcl installation required by [AGENTS.md](../../AGENTS.md):

```text
/home/syazwan/.vscode-server/extensions/oracle.sql-developer-26.2.1-linux-x64/dbtools/sqlcl/bin/sql
```

On a fresh database intended for the package-only implementation, run from the repository root with the appropriate saved ADMIN connection and exact DB_NAME:

```bash
python3 scripts/db.py preflight --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py provision --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py install --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py verify-admin --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
```

For an actual runtime-login check, configure a saved SQLcl connection for DB_HEALTH_AGENT using the same database network settings and no saved password; the helper supplies its generated password:

```bash
python3 scripts/db.py verify-runtime --connection 'YOUR_RUNTIME_CONNECTION' --expected-db YOUR_DB_NAME
```

The verification boundaries above apply: do not run these assertions as acceptance checks for an account extended with the current Select AI grants. SQLcl and PAF connections are configured separately. Never put passwords, wallets, live query results or connection exports into tracked files.
