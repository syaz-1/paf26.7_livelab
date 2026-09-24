> Superseded: the user confirmed same-schema visibility on 2026-09-24.
> All five wrappers are now deployed by db/05_runtime_api.sql. Do not run the
> diagnostic cleanup below against the active integration.

# Same-schema discovery test

The Agent Factory PL/SQL Executor dropdown returned no matches for DB_HEALTH_API,
although the runtime account could discover and execute the owner package in SQLcl.
At the user's request, a one-function package is added in the connection schema:

`DB_HEALTH_AGENT.DB_HEALTH_API.GET_DATABASE_OVERVIEW()` returns CLOB.

This wrapper delegates to
`DB_HEALTH_OWNER.DB_HEALTH_API.GET_DATABASE_OVERVIEW()`. It retains the same
package/function name and return type as the original to test schema ownership.
No new privileges are granted; ADMIN deploys the wrapper. DB_HEALTH_AGENT still
has no CREATE PROCEDURE or monitoring-view SELECT privileges.

Deployment and verification:

```bash
python3 scripts/db.py install-discovery-test --connection 'demo adb sg admin' --expected-db G2C3435895384DA_DEMO
python3 scripts/db.py verify-discovery-test --connection 'demo adb sg health agent' --expected-db G2C3435895384DA_DEMO
```

Installation refuses to replace an existing runtime package. Verification checks
USER_PROCEDURES, USER_ARGUMENTS and a real function call as DB_HEALTH_AGENT.

In Agent Factory, refresh the page or re-add the executor node, select the same
runtime database source, and filter by DB_HEALTH_API. Look for GET_DATABASE_OVERVIEW
under DB_HEALTH_AGENT. A successful SQLcl test does not establish dropdown behavior.
If it appears, that supports an ownership-dependent discovery limitation; actual
execution in Agent Factory still needs testing. Do not move all five routines or
broaden grants before this UI check.

The test package remains installed for the UI check. To remove it later, after
removing any Agent Factory references, a DBA can explicitly run:

```sql
DROP PACKAGE DB_HEALTH_AGENT.DB_HEALTH_API;
```

This cleanup is not automatically executed. The original owner package is retained.
