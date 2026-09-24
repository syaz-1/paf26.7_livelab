# Local project instructions

This is a template. Copy to the repository root as AGENTS.md, replace placeholders with verified local values, and keep that copy untracked. Never put passwords, tokens, signing keys or wallet contents here.

## Project scope

- Read README.md for the current Select AI Bridge flow and test status.
- For setup or reconnection, follow docs/setup/README.md and the verified local handoff in .local/environment.md. Neither this file nor the worksheet overrides helper constants.
- Runtime database login and monitoring-view schema: DB_HEALTH_AGENT.
- ADMIN is for explicitly requested provisioning work only.
- Database changes are not part of local environment setup.
- For the older package implementation, read docs/legacy-plsql/README.md before changing it. Keep its API limited to fixed queries with bind parameters; do not add generic SQL execution or write operations.

## Local database tooling

- SQLcl executable bundled with the Oracle SQL Developer extension: <VERIFIED_ABSOLUTE_SQLCL_PATH>
- Saved runtime SQLcl connection: <VERIFIED_CONNECTION_NAME_OR_NOT_CONFIGURED>
- Expected database identity (DB_NAME): <VERIFIED_DB_NAME_OR_NOT_CONFIGURED>
- Confirm the intended database and SESSION_USER before database work.
- Do not assume saved connections or credentials from another developer exist locally.

## Local PAF target

- PAF credentials and URL: .env (never echo its contents).
- Intended PAF database source ID: <VERIFIED_DATABASE_SOURCE_ID_OR_NOT_CONFIGURED>
- Intended Select AI profile: <VERIFIED_PROFILE_NAME_OR_NOT_CONFIGURED>
- Intended monitoring flow ID: <VERIFIED_FLOW_ID_OR_NOT_CONFIGURED>
- TLS certificate verification: <VERIFIED_PIN_STATUS_OR_NOT_CONFIGURED>
- Existing Python helpers contain environment-specific constants. This file documents local settings; it does not override those constants. Review the code and README setup checklist before running helpers against another deployment.

## Local artifacts

- Keep AGENTS.md, .env, wallets, credentials, connection exports, live rows and AI/session traces out of tracked files.
- Save private outputs under .local/; restrict directory/file permissions appropriately.
- Preserve existing local configuration. Ask for missing nonsecret settings; have the user enter secrets through approved local fields or their secret store.
- Do not copy another user's Codex authentication, global settings, plugins or session history. They are not required project configuration.
