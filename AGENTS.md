# Database tooling

Use the SQLcl installation bundled with the Oracle SQL Developer extension:

`/home/syazwan/.vscode-server/extensions/oracle.sql-developer-26.2.1-linux-x64/dbtools/sqlcl/bin/sql`

Keep passwords, wallets, connection exports and live query results out of tracked files.
The runtime database identity is DB_HEALTH_AGENT; DB_HEALTH_OWNER owns the
read-only monitoring package and has no login. ADMIN is for provisioning only.
Use fixed queries and bind parameters. Never add a generic SQL execution tool
or write operation to DB_HEALTH_API.
