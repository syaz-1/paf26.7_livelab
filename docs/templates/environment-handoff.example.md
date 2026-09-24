# Local environment handoff

Copy this file to .local/environment.md. It is a human/agent worksheet, not an automatically loaded application configuration. Store only nonsecret values and secret-store references here. Use NOT_CONFIGURED for unknown items; do not infer production values from examples.

## Ownership and purpose

- Environment name and purpose: NOT_CONFIGURED
- Existing deployment or new setup: NOT_CONFIGURED
- Environment owner/contact: NOT_CONFIGURED
- Database administrator/contact: NOT_CONFIGURED
- Model/provider administrator/contact: NOT_CONFIGURED
- Last verified date: NOT_CONFIGURED
- Approved operations for this handoff: NOT_CONFIGURED

## Developer machine

- OS / shell: NOT_CONFIGURED
- Repository absolute path: NOT_CONFIGURED
- Python executable and version (3.9+): NOT_CONFIGURED
- Oracle SQL Developer extension location/version: NOT_CONFIGURED
- Bundled SQLcl absolute path and version: NOT_CONFIGURED
- VPN/proxy/access prerequisites: NOT_CONFIGURED

## PAF application

- HTTPS URL, including port when applicable: NOT_CONFIGURED
- PAF version: NOT_CONFIGURED
- PAF username: NOT_CONFIGURED
- PAF password secret-store reference (not the password): NOT_CONFIGURED
- Trusted TLS certificate SHA-256 fingerprint: NOT_CONFIGURED
- Fingerprint verified with / date: NOT_CONFIGURED
- Browser login verified: NOT_CONFIGURED
- Python pinned-client login verified: NOT_CONFIGURED
- Required workflow/data-source/model permissions verified: NOT_CONFIGURED

## Database connection

- Database environment/identifier: NOT_CONFIGURED
- Expected Oracle DB_NAME: NOT_CONFIGURED
- Expected container name: NOT_CONFIGURED
- Runtime user: DB_HEALTH_AGENT
- Runtime password secret-store reference: NOT_CONFIGURED
- Connection method (wallet/TNS or approved alternative): NOT_CONFIGURED
- TNS alias / service name: NOT_CONFIGURED
- Database host and port, if applicable: NOT_CONFIGURED
- TLS / mTLS requirements: NOT_CONFIGURED
- Wallet source and expiry/rotation owner: NOT_CONFIGURED
- Local wallet directory (prefer .local/wallet): NOT_CONFIGURED
- Wallet password secret-store reference, if needed: NOT_CONFIGURED
- Saved SQLcl runtime connection name: NOT_CONFIGURED
- Saved ADMIN connection name, only if provisioning is assigned: NOT_CONFIGURED
- SQLcl runtime identity check passed: NOT_CONFIGURED
- Monitoring view verification passed: NOT_CONFIGURED
- Database preparation complete (five views and required grants): NOT_CONFIGURED

## PAF database source

- Display name: NOT_CONFIGURED
- Internal database source ID: NOT_CONFIGURED
- Runtime username verified: NOT_CONFIGURED
- PAF-side wallet/connection configuration complete: NOT_CONFIGURED
- PAF database connection test passed: NOT_CONFIGURED

## Agent model registration (PAF host -> model)

- Registration name: NOT_CONFIGURED
- Provider / model identifier: NOT_CONFIGURED
- Region / endpoint: NOT_CONFIGURED
- Compartment/project identifier, if applicable: NOT_CONFIGURED
- Authentication method and secret-store references: NOT_CONFIGURED
- Required OCI user/tenancy IDs and signing-key fingerprint, if applicable: NOT_CONFIGURED
- Tool-calling support verified: NOT_CONFIGURED
- Connection test passed: NOT_CONFIGURED

## Select AI profile (database -> model)

- Database owner of credential and profile: DB_HEALTH_AGENT
- Provider credential name: NOT_CONFIGURED
- Provider authentication method and secret-store references: NOT_CONFIGURED
- Profile name: NOT_CONFIGURED
- Provider / model identifier: NOT_CONFIGURED
- Region / endpoint / API format, if applicable: NOT_CONFIGURED
- Compartment/project identifier, if applicable: NOT_CONFIGURED
- Max tokens: NOT_CONFIGURED
- NL2SQL / RAG settings: NOT_CONFIGURED
- Object list mode / enforce_object_list setting: NOT_CONFIGURED
- Enforce setting approval/rationale: NOT_CONFIGURED
- Object list: DB_HEALTH_AGENT.MONITOR_DATABASE_OVERVIEW, MONITOR_SESSIONS, MONITOR_STORAGE_USAGE, MONITOR_JOB_RUNS, MONITOR_SQL_WORKLOAD
- Profile validation passed: NOT_CONFIGURED
- Real monitoring query passed: NOT_CONFIGURED

## Agent flow and validation

- Flow display name and ID: NOT_CONFIGURED
- Agent model registration selected: NOT_CONFIGURED
- Bridge database source and profile selected: NOT_CONFIGURED
- Bridge action: NOT_CONFIGURED
- Agent temperature: NOT_CONFIGURED
- Memory enabled / disabled: NOT_CONFIGURED
- Publication and sharing status: NOT_CONFIGURED
- Canonical instructions version/date: NOT_CONFIGURED
- Integration endpoint/key reference, only if integration is required: NOT_CONFIGURED
- scripts/db.py SQLCL adaptation needed/completed: NOT_CONFIGURED
- scripts/paf_client.py certificate pin adaptation needed/completed: NOT_CONFIGURED
- scripts/test_monitoring_agent.py source ID/profile adaptation needed/completed: NOT_CONFIGURED
- Smoke tests passed / date: NOT_CONFIGURED
- Full regression report/private output directory: NOT_CONFIGURED
- Known limitations / outstanding actions: NOT_CONFIGURED
