# New contributor setup and environment handoff

Use this guide when another person clones the repository, connects to an existing deployment, or rebuilds the monitoring Agent in a different environment. It covers local files, database connectivity, PAF resources, model settings and validation. The [main README](../../README.md) describes the implemented Agent; this guide explains how to obtain and verify the configuration required to work with it.

A clone contains code, templates and reviewed reports. It does not contain passwords, wallets, PAF resource registrations, saved SQLcl connections or previous local traces. Those are separate parts of the environment.

## 1. Choose the setup path

| Your situation | What to do |
|---|---|
| Only read/edit documentation or export Word files | Set up Git and Python; no database, PAF or provider credentials are needed |
| Connect to the existing working Agent | Obtain access and target identifiers; verify the existing resources without provisioning or replacing them |
| Database prepared, but PAF configuration is missing | Complete local access setup here, then follow the [PAF-only LiveLab](../livelab-paf-only/README.md) |
| New database-side monitoring setup is required | Have the DBA follow the [complete LiveLab](../livelab/README.md), then configure PAF |
| Maintain the older PL/SQL tool implementation | Use the [legacy PL/SQL README](../legacy-plsql/README.md); its permission checks differ from Select AI |

The project assumes an installed PAF instance and an existing Autonomous Database. Infrastructure installation, tenancy access and account recovery must be provided by the environment owner. Connecting to an existing environment does not require creating another database user or resetting a password.

## 2. Obtain the handoff from the environment owner

Copy the [environment handoff worksheet](../templates/environment-handoff.example.md) to `.local/environment.md` and fill in verified values. The worksheet records nonsecret details and secret-store references, not passwords or signing keys.

Ask the appropriate owner for:

| Area | Required information | Usually supplied by |
|---|---|---|
| PAF access | HTTPS URL/port, your login, access permissions, version, trusted certificate fingerprint | PAF administrator |
| Database | Intended environment, expected DB_NAME/container, runtime username, password access, connection method and service/TNS alias | DBA |
| Database network | Required VPN/routes, allowed client locations, database host/port where applicable, TLS/mTLS method | DBA/network administrator |
| Wallet | Approved download/transfer location, password if applicable, expiry and rotation contact | DBA |
| PAF database source | Display name, internal source ID, connection identity and whether it is shared | PAF administrator |
| Agent LLM | Registration name, provider, model, region/endpoint, authentication and tool-calling capability | Model/PAF administrator |
| Select AI | Credential/profile names and owner, model/region/compartment, object list and enforcement setting | DBA/model administrator |
| Agent workflow | Flow name/ID, access/sharing, publication, memory setting and final instructions | Flow owner |
| Integration, if needed | Correct flow-specific endpoint and key provisioned for your use | Flow owner |

The PAF login password, database login password, wallet password, OCI signing key and PAF integration key are different credentials. None can substitute for another. The PAF UI/owner-API test runner uses your PAF login, not the database password or an integration key.

## 3. Prepare your local workspace

1. Obtain the repository URL from the project owner and clone it, or open your existing checkout.
2. Install Git and Python **3.9 or newer** for the supplied Python scripts. These scripts and the DOCX exporter use the standard library; this project does not require a pip dependency installation for them.
3. If doing database work, install the Oracle SQL Developer extension and locate its bundled SQLcl. The absolute path in the original environment is only an example; use the executable actually installed on your machine.
4. Check your tools:

   ```bash
   git --version
   python3 --version
   ```

5. Create missing local files from the repository root. On Linux/macOS:

   ```bash
   mkdir -p .local
   chmod 700 .local
   cp -n .env.example .env
   cp -n docs/templates/AGENTS.local.example.md AGENTS.md
   cp -n docs/templates/environment-handoff.example.md .local/environment.md
   chmod 600 .env AGENTS.md .local/environment.md
   ```

   `cp -n` preserves existing files. On another OS, copy only missing files and restrict their permissions using the equivalent filesystem controls.

6. Fill in the worksheet and `AGENTS.md` with verified local paths and target references. Leave unknown values marked `NOT_CONFIGURED` until supplied or verified.

`AGENTS.md` supplies local instructions to a coding agent. `.local/environment.md` is a human/agent handoff record. Neither file is parsed by the Python helpers as runtime configuration.

## 4. Configure .env for PAF access

The exact keys consumed by `scripts/paf_client.py` are:

```dotenv
agent_factory_url=https://YOUR_PAF_HOST:8080/agentFactory/
agent_factory_username=YOUR_PAF_USERNAME
agent_factory_password=REPLACE_LOCALLY
```

Edit `.env` locally using the correct URL/port and your own credentials. Do not paste the populated file into chat or commit it. Use HTTPS and do not embed credentials inside the URL.

The small parser accepts literal `key=value` lines and matching outer quotes. It does not expand shell variables or read database/model configuration from additional invented keys. Avoid trailing inline comments on values. Do not `source .env` to run these Python scripts; the client reads the file itself.

| Local file | Purpose | Automatically read by |
|---|---|---|
| `.env` | PAF URL, username and password | `scripts/paf_client.py` |
| `AGENTS.md` | Machine-specific coding-agent instructions | The coding agent's instruction discovery |
| `.local/environment.md` | Connection/profile/flow handoff worksheet | Nothing automatically |
| `.local/wallet/` or approved secure location | Database network authentication files, when required | SQLcl/client configured to use that location |
| `.local/db_health_agent.password` | Password generated by the original provisioning helper | Specific runtime-verification actions in `scripts/db.py` |
| `.local/paf-tests/` | Private regression responses and metadata | Test runners write here |

The generated database-password file is not required for the PAF test runner. Do not create it with a made-up password or run provisioning to replace an existing account's credential. Use the existing authorized credential and your chosen connection method.

## 5. Verify TLS and network paths

There are separate network paths to verify:

```text
Your browser / Python client → PAF HTTPS endpoint
Your SQLcl client            → Autonomous Database (for direct DB work)
PAF server                  → Autonomous Database
PAF Agent model runtime     → configured model provider
Autonomous Database         → Select AI model provider
```

A successful connection on one path does not establish the others. Apply the endpoint-specific VPN/proxy/routes and ports supplied by the administrator, rather than assuming the developer machine and PAF host share network access.

The existing Python client uses a SHA-256 certificate pin in `scripts/paf_client.py` (`KNOWN_CERT_SHA256`). Obtain and independently verify the expected deployment certificate fingerprint with the administrator before adapting this value. The pin is compared before PAF login credentials are sent. Certificate rotation requires re-verification; do not remove the comparison or automatically accept an unfamiliar certificate.

For browser use, have the administrator provide a correctly configured, trusted HTTPS endpoint. A matching fingerprint for the Python client does not repair browser trust or hostname errors.

Record the verified URL, pin and verification date in the private handoff worksheet. The current scripts do not consume a certificate-pin variable from `.env`; changing the worksheet alone is not sufficient.

## 6. Configure and verify the database connection

Skip this section if your task is purely PAF UI configuration and the facilitator has already verified the database. You still need the PAF-side connection check in Section 7.

### Saved SQLcl connection

1. Locate the SQLcl bundled with your Oracle SQL Developer extension. Verify its executable/version and record the absolute path in local `AGENTS.md`.
2. Obtain the approved service/TNS alias and network method. For a wallet-based connection, store the wallet under `.local/wallet/` or the approved secure location, keeping its companion files together.
3. Use the installed Oracle connection manager/SQL Developer connection UI to create a saved connection with the approved wallet/service and **DB_HEALTH_AGENT** login. Test it using the supplied runtime password.
4. Record the exact saved connection name. Saved SQLcl connections are local to the relevant user/profile; a name from another machine does not create one here.
5. Start the discovered SQLcl executable with `/nolog` and connect interactively:

   ```sql
   connect -name "YOUR_RUNTIME_CONNECTION"
   ```

   Let the client use its configured credential handling or prompt. Do not put a password in the shell command line.

6. Check identity with this fixed read-only query:

   ```sql
   select sys_context('USERENV','SESSION_USER') as session_user,
          sys_context('USERENV','DB_NAME') as database_name,
          sys_context('USERENV','CON_NAME') as container_name
   from dual;
   ```

7. Match the result to the owner's expected database/container and `DB_HEALTH_AGENT` before proceeding. Record the nonsecret identity values.
8. From a SQLcl session started in the repository root, run the current view check, replacing the argument with the expected DB_NAME:

   ```sql
   @docs/livelab/files/verify-monitoring.sql YOUR_EXPECTED_DB_NAME
   ```

   This reads the five prepared views with bounded results. Keep any saved output private. Empty data is possible; invalid objects or missing permissions require DBA review.

For the Select AI flow, the five views must be valid and readable in `DB_HEALTH_AGENT`. The DBA prepares the needed monitoring-source and cloud-package grants using the complete LiveLab. ADMIN access is not required for an ordinary runtime connection or PAF participant.

If the database is not prepared, use the first-time setup path explicitly. Do not rerun scripts against existing objects, reset passwords or revoke grants just because a legacy verification test fails.

## 7. Configure PAF resources independently

Use the [PAF-only LiveLab](../livelab-paf-only/README.md) for exact field-by-field UI steps. Record the final settings in `.local/environment.md`.

### Database source

- Reuse the intended source when already registered, or create the assigned one under **Data Sources → Database**.
- Configure `DB_HEALTH_AGENT` with the correct service and wallet/network method, then test connectivity **from PAF**.
- A wallet path on your laptop is not a wallet path inside the PAF host/container. Upload/configure the wallet through the supported PAF connection method.
- Record both the source's display name and internal ID. Scripts check the ID, not just the label.

### Agent LLM registration

- In **LLM Management**, reuse or create the approved tool-capable model connection.
- Record provider, model identifier, registration name, region/endpoint, compartment/project and credential reference.
- For OCI API signing, obtain the required user/tenancy identifiers, key fingerprint and private signing key through the approved process. Enter secrets only in the provider's designated configuration fields.
- Test the model connection. A later successful Agent tool invocation verifies more than simple model connectivity.

### Select AI provider credential and profile

- In **Settings → Select AI Framework**, select the intended database source.
- Reuse/create the approved database-owned provider credential and profile through the UI. Their ownership must match the connection's database user.
- Record the exact profile name, provider/model, region, compartment and any endpoint/API-format setting required by that deployment. These are independent of the Agent model registration.
- Select the five `DB_HEALTH_AGENT.MONITOR_*` views described in the main README. Enable NL2SQL, disable RAG for this MVP, use object-list mode All and Max Tokens 4096.
- Preserve the approved enforcement policy. The original environment used enforcement Off as an investigated workaround; do not silently assume every deployment needs the same setting.
- Validate the profile, then test a real Run SQL monitoring request. Credential/profile validation alone does not prove query execution works.

### Agent flow

- Reuse the intended flow or create a uniquely named one using Chat Input, Agent, Select AI Bridge and Chat Output.
- Set Bridge to Profile / the intended database and profile / Run SQL.
- Select the Agent model, temperature 0.01, and paste the complete canonical instructions from `docs/monitoring-agent-instructions.txt`.
- Connect Chat Input Message → Agent Prompt, Bridge Tool → Agent Tools, and Agent Message → Chat Output Message.
- Save and verify memory is disabled for the baseline tests. Record the flow ID, publication/sharing state and date.
- Do not assume another person's flow ownership or resource access is inherited by your PAF login.

## 8. Review script compatibility before automation

The repository is not yet fully portable through `.env` alone. The following values are currently embedded in code or passed explicitly:

| Component | Deployment-specific setting | What the new contributor must do |
|---|---|---|
| `scripts/paf_client.py` | `KNOWN_CERT_SHA256` | Independently verify and adapt the target certificate pin |
| `scripts/db.py` | `SQLCL` absolute path | Point the helper to the installed bundled SQLcl when using it |
| `scripts/test_monitoring_agent.py` | Expected database source ID and profile | Align the assertions with the reviewed intended flow; do not remove them |
| Current Agent runner CLI | `--agent-id` | Supply the correct four-node flow ID |
| `scripts/test_select_ai.py` | Fixed older flow ID, source ID/profile and integration-key input | Use only for the earlier direct Select AI flow, with separately reviewed settings |
| Older SQL deployment/diagnostic files | Recorded DB_NAME and account assumptions | Review target checks before use; do not blindly replace all identifiers |

Changing `AGENTS.md` or the handoff worksheet does not modify these settings. No `SQLCL_PATH`, `DB_PASSWORD`, `PAF_AGENT_ID` or similar extra `.env` key is currently read by these helpers. Do not document such keys as working configuration without implementing support.

Any needed changes to tracked code should be explicit and reviewed. Do not rewrite another environment's settings or remove identity/TLS checks to make automation pass. The current test runner also expects a pre-existing private `.local/paf-tests/` parent; create it before the first run on a fresh clone.

## 9. Validate access in increasing scope

1. **Local checks:** confirm Python/SQLcl as needed, required local files and ignore rules. No remote calls are required to edit documentation or regenerate Word files.
2. **Browser checks:** sign in to the intended PAF deployment and verify access to the database source, model and assigned flow.
3. **Connection checks:** test the PAF database and model connections and Select AI profile. If using SQLcl, verify its runtime database identity separately.
4. **Playground smoke tests:** use fresh conversations for `Show the database identity and service name.`, `asdf qwer zxcv`, and `Was it slower yesterday than today?`. Expect actual identity, clarification and an unsupported-history explanation respectively.
5. **Automated regression:** after target/pin alignment and permission to exercise the configured models, run from the repository root:

   ```bash
   mkdir -p .local/paf-tests
   chmod 700 .local .local/paf-tests
   python3 scripts/test_monitoring_agent.py --agent-id YOUR_VERIFIED_FLOW_ID
   ```

   This invokes PAF and the configured models, creates chat history, and may query monitoring data. It is not a local-only unit test. It uses the PAF login in `.env` and does not require an integration API key.

6. Review the private results and record behavioral outcomes. HTTP 200 alone is not a pass. Save a sanitized summary, not raw live data, in a tracked report if appropriate.

A 401/403 usually requires checking credentials and resource permissions. A certificate mismatch requires verified pin review. A profile/object error requires confirming the source, owner and selected views. See the LiveLab troubleshooting table for model/token and query-scope errors.

The legacy package privilege checks are not acceptance checks for a Select AI-enabled account. Use the current view-verification script and current Agent runner for this path.

## 10. Keep local configuration local

Run:

```bash
git check-ignore -v AGENTS.md .env .local/
git ls-files -- AGENTS.md .env .local/
git status --short
```

The first command should identify ignore rules, and the second should print nothing. The status output helps review any source adaptations before committing. An ignore rule does not retroactively untrack a file already in Git.

Store connection exports, complete wallet archives/directories, raw database responses and exported AI/session traces under `.local/` or the approved secret location. The repository's suffix patterns do not cover every possible extracted wallet filename outside that directory. Do not copy a developer's Codex account authentication or global session history to recreate this project.

A PAF integration key is optional and distinct from the owner-API test login. If an integration is needed, create/obtain one scoped to the intended flow using the PAF Integration UI and keep it in the approved secret store. Do not reuse keys from transcripts or another flow. No integration secret belongs in the tracked worksheet/template.

## 11. Reconnect later

1. Read the private handoff worksheet for the last verified target and date.
2. Check for expired/rotated PAF credentials, database passwords, wallets, certificates and provider keys with their owners; update only the affected connection settings.
3. Confirm SQLcl paths after extension upgrades, and PAF resource IDs if resources were recreated or imported.
4. Re-test the relevant connection path and a small monitoring query before a broad regression.
5. Update verification dates and outstanding issues in the worksheet. Keep the runtime identity and database target checks.

You can reconstruct configuration files from templates and verified inputs. You cannot reconstruct the original passwords, private keys, wallet contents or PAF resources simply from a Git clone. Missing access must be supplied by the authorized environment owner.
