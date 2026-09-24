# Autonomous Database Health Assistant

A database monitoring MVP built with Oracle Private Agent Factory (PAF), an Agent node and Select AI Bridge. It answers supported monitoring questions, clarifies malformed requests, and explains the limits of the available evidence.

This README covers the current Select AI flow, its LiveLabs and validation evidence. The recorded implementation and test status below is from **24 September 2026**.

## Start here

New to this checkout or connecting from another machine? Read the [complete environment setup and handoff guide](docs/setup/README.md) first.

| Starting point | Guide | Word document |
|---|---|---|
| Database already prepared; configure everything through PAF | [PAF configuration-only LiveLab](docs/livelab-paf-only/README.md) | [Download DOCX](docs/livelab-paf-only/ADB_Health_Monitoring_Agent_PAF_Only_LiveLab.docx) |
| Need database preparation and PAF configuration | [Complete LiveLab](docs/livelab/README.md) | [Download DOCX](docs/livelab/ADB_Health_Monitoring_Agent_LiveLab.docx) |

The PAF-only lab assumes the runtime account, permissions, monitoring views and provider access are ready. Neither guide installs PAF or provisions an Autonomous Database. Both are local LiveLabs-style workshop packages, not published Oracle LiveLabs offerings.

For the existing implementation, open **Workflows → ADB Health Monitoring Agent MVP → Playground**. See the [saved flow configuration](docs/monitoring-agent-flow.md) and [complete Agent instructions](docs/monitoring-agent-instructions.txt).

## Current Agent flow

```text
Chat input ───► Agent ───► Chat output
                 ▲
                 │ Tool
          Select AI Bridge
          Profile + Run SQL
                 │
                 ▼
          DB_HEALTH_AGENT
          MONITOR_* views
                 │
                 ▼
          Oracle monitoring views
```

| Setting | Recorded configuration |
|---|---|
| Flow | ADB Health Monitoring Agent MVP |
| Flow ID | `5C2A338670CA1162E0634815000AC353` |
| Database source | ADB HEALTH MVP |
| Runtime database login | DB_HEALTH_AGENT |
| Select AI profile | DB_HEALTH_AGENT |
| Bridge mode / action | Profile / Run SQL |
| Agent model registration | llm_model_entry (OCI), temperature 0.01 |
| Agent memory | Disabled |
| Select AI output token limit | 4096 |
| Object-list mode / enforcement | All / disabled for the approved MVP workaround |
| Last observed publication state | Published |

The Agent's model registration and the database's Select AI profile are separate configurations. Select AI generates and executes queries; the Agent validates requests and explains returned results. A standalone Chat Input → Select AI → Chat Output flow is retained as an earlier test path, but it does not provide the same conversational behavior.

The four-node flow connects Chat Input **Message** to Agent **Prompt**, Select AI Bridge **Tool** to Agent **Tools**, and Agent **Message** to Chat Output **Message**. General slowdown checks cover sessions and cumulative SQL. Overall health uses a compact identity/session/storage/job summary followed by a cumulative SQL check.

## Monitoring coverage

All five selected views belong to `DB_HEALTH_AGENT`:

| View | Evidence | Scope limitation |
|---|---|---|
| `MONITOR_DATABASE_OVERVIEW` | Database identity, service and observation time | Reachability is not overall health |
| `MONITOR_SESSIONS` | Active or blocked user sessions, waits and blocker IDs | Current snapshot only |
| `MONITOR_STORAGE_USAGE` | Tablespace used bytes, capacity and percentage | Not Autonomous service provisioned storage or OCI StorageUtilization |
| `MONITOR_JOB_RUNS` | Retained Scheduler runs with all statuses and timestamps | Not job definitions or a live running-job inventory |
| `MONITOR_SQL_WORKLOAD` | Cached per-instance SQL counters and elapsed time | Cumulative counters, not historical daily performance |

`COLLECTED_AT_UTC` is generated at observation time; it is not a stored sample date. Use the retained job event timestamps for job-history windows. An empty failed-job result does not prove every expected job ran. The earlier `MONITOR_FAILED_JOBS` view remains for compatibility but is not one of the five selected profile objects.

Same-schema wrapper views make the monitoring objects discoverable in the tested PAF picker. The Select AI flow queries these views directly as `DB_HEALTH_AGENT`.

## Database access and MVP limits

`DB_HEALTH_AGENT` is the runtime login and owns the monitoring views. ADMIN is used for provisioning only; application objects are not installed in ADMIN or SYS.

For the Select AI path, the runtime account has direct SELECT access to five SYS monitoring sources and execution access to `DBMS_CLOUD` and `DBMS_CLOUD_AI`. The read-only wrapper views expose a smaller column set, but do not remove the account's underlying privileges.

Object-list enforcement was disabled after storage/job queries encountered `ORA-20004` despite naming selected views. Disabling enforcement allowed those checks to execute; the exact internal cause remains unproven. The object list now guides metadata selection rather than enforcing the five-view boundary. See the [validation investigation](tests/paf/select-ai-validation-investigation-2026-09-24.md).

The Agent is instructed to perform monitoring only. Its instructions do not guarantee input validation, access isolation or SQL correctness. SQL meaning and causal conclusions still require review. A privately deployed PAF application can call hosted models; use approved destinations for prompts, schema metadata, returned monitoring data and traces.

## Validation status

The new Agent was tested with the original 21 prompts plus three out-of-scope questions:

- All 24 requests returned HTTP 200; transport success was not graded as behavioral success.
- All ten clarification/scope cases passed in that baseline run: nonsense, invalid limits/durations, ambiguous overnight timing, unsupported historical comparison, and unrelated questions.
- Initial multi-check completion and explanation issues were identified and the Agent instructions were revised.
- Targeted retests returned complete slowdown/workload answers, a retained-log caveat, and a complete overall-health answer after the two-call adjustment.
- **The full 24-case suite has not been rerun after the final overall-health adjustment.** Some wording and causal interpretation still warrant review; this is not an all-tests-pass claim.

Read the [current Agent test report](tests/paf/results-monitoring-agent-2026-09-24.md) and [failed-query investigation](tests/paf/select-ai-failed-case-investigation-2026-09-24.md). The [24 workshop prompts](docs/livelab-paf-only/files/test-prompts.md) provide expected behavior for manual Playground tests.

### Run the current Agent regression

In the configured project environment:

```bash
python3 scripts/test_monitoring_agent.py --agent-id 5C2A338670CA1162E0634815000AC353
```

The runner reads `agent_factory_url`, `agent_factory_username` and `agent_factory_password` from the ignored `.env` file. It uses the authenticated owner run endpoint, creates distinct chat rooms and writes private responses under `.local/paf-tests/`. No integration API key is needed for this runner. Running it invokes the configured models and monitoring queries.

The runner is tied to the reviewed database source ID, profile and four-node graph; `scripts/paf_client.py` pins the reviewed server certificate. For another deployment, review these values and verify its certificate before adapting the client. Do not bypass those checks merely to make a different environment run. The script collects evidence; final answers require behavioral review and do not include complete generated SQL/tool traces.

## Setup and handoff for another contributor

Start with the [complete environment setup guide](docs/setup/README.md). It covers a fresh checkout, reconnecting to an existing deployment, `.env`, database credentials and wallets, SQLcl saved connections, network/TLS checks, PAF database/model/profile/flow settings, script adaptation, testing and later credential/certificate rotation.

A Git clone does not recreate database accounts, saved connections, PAF resources, passwords or wallets. Obtain the intended environment and access details from the appropriate owner; do not reuse recorded instance IDs as defaults for a different deployment.

### What must be configured

| Layer | Configuration | Where it lives |
|---|---|---|
| Local tools | Git, Python 3.9+, bundled SQLcl for DB work | Developer machine |
| PAF client login | URL, username and password | Ignored `.env` |
| Database connection | Expected DB_NAME, runtime user, service/TNS alias, network method, wallet and credential | SQLcl connection manager and approved local secret location |
| PAF database source | Runtime connection, wallet/service settings and internal source ID | PAF Data Sources |
| Agent model | Registration, provider/model, endpoint/region, authentication and tool calling | PAF LLM Management |
| Select AI | Database-owned credential/profile, provider model and five-view object list | PAF Select AI Framework |
| Agent flow | Model, Bridge source/profile/action, instructions, memory and flow ID | PAF Agent Builder |
| Script compatibility | Verified TLS pin, SQLcl path, expected source/profile IDs | Existing helper constants; see the setup guide |
| Local handoff | Verified nonsecret values, secret-store references and dates | Ignored `.local/environment.md` |
| Coding-agent instructions | Local paths, target references and work rules | Ignored root `AGENTS.md` |

Use the [environment handoff worksheet](docs/templates/environment-handoff.example.md) to collect the details. It is a checklist for a person or coding agent, not runtime configuration automatically read by the scripts.

### Create missing local files

From the repository root on Linux/macOS:

```bash
mkdir -p .local/paf-tests
chmod 700 .local .local/paf-tests
cp -n .env.example .env
cp -n docs/templates/AGENTS.local.example.md AGENTS.md
cp -n docs/templates/environment-handoff.example.md .local/environment.md
chmod 600 .env AGENTS.md .local/environment.md
```

These copy commands preserve existing files. Fill in the local copies using verified values and approved secret-entry methods. The exact `.env` keys currently consumed by the PAF client are `agent_factory_url`, `agent_factory_username` and `agent_factory_password`; see [.env.example](.env.example).

**The repository is not fully configurable through `.env` alone.** Local instructions and the worksheet do not override the SQLcl path, certificate pin or database/profile assertions embedded in the helpers. Follow the setup guide's compatibility table before automation. Database passwords, wallets, provider keys and connection registrations require separate configuration.

### Starter prompt for Codex

Open the checkout and provide this prompt:

```text
Read README.md and docs/setup/README.md for the complete environment setup.
Inspect local tools without printing credentials. Preserve existing files.
Create missing AGENTS.md, .env and .local/environment.md from their templates.
Discover the bundled SQLcl path and record verified nonsecret local settings.
Review all required PAF, database, wallet, TLS, model, Select AI and flow fields
in the handoff worksheet. Ask for missing target values and access details;
leave passwords/keys for me to enter locally through approved secret methods.
Identify helper constants that need adaptation; don't bypass identity or TLS
checks. Do not provision resources, reset credentials or run model-backed tests
as part of local bootstrap. Report readiness and remaining setup by layer.
```

Codex discovers `AGENTS.md` when it starts a run/session. After creating or changing it, start a new session and ask which instruction files were loaded. Explicitly direct the first setup session to read the README and setup guide. See [OpenAI's AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

To check that local files remain untracked:

```bash
git check-ignore -v AGENTS.md .env .local/
git ls-files -- AGENTS.md .env .local/
```

The second command should print nothing. Keep wallets, exports, live query results and AI/session traces under `.local/` or the approved secret location. No copied Codex login, global settings or session history is required. The full guide provides the ordered connection checks and reconnect checklist.

## Database setup and tooling

For the current Select AI path, follow the [complete LiveLab](docs/livelab/README.md). It includes:

- [First-time monitoring grants and views](docs/livelab/files/prepare-monitoring.sql), run as ADMIN against an explicitly checked database with an existing runtime account.
- [Runtime view verification](docs/livelab/files/verify-monitoring.sql), run as DB_HEALTH_AGENT.

Use the SQLcl bundled with the Oracle SQL Developer extension. The configured project environment uses:

```text
/home/syazwan/.vscode-server/extensions/oracle.sql-developer-26.2.1-linux-x64/dbtools/sqlcl/bin/sql
```

Keep passwords, wallets, connection exports, live query results and diagnostic logs out of tracked files. `.env`, `.local/`, wallet files and logs are ignored. SQLcl and PAF have separate connection stores; verify PAF connectivity independently.

## Repository map

| Path | Purpose |
|---|---|
| `docs/livelab-paf-only/` | PAF-only workshop, DOCX, instructions and test prompts |
| `docs/livelab/` | Complete workshop, DOCX and database preparation assets |
| `docs/monitoring-agent-flow.md` | Recorded current flow settings |
| `docs/monitoring-agent-instructions.txt` | Canonical current Agent instructions |
| `db/` | Original package deployment, monitoring grants/views and legacy tests |
| `scripts/test_monitoring_agent.py` | Current four-node Agent regression |
| `scripts/test_select_ai.py` | Earlier direct Select AI flow regression |
| `docs/legacy-plsql/README.md` | Legacy PL/SQL architecture, setup and verification |
| `tests/paf/` | Prompts, reviewed reports and investigations |
| `docs/setup/README.md` | Complete contributor setup, connection and reconnect guide |
| `docs/templates/environment-handoff.example.md` | Nonsecret environment handoff worksheet |
| `docs/templates/AGENTS.local.example.md` | Portable template for ignored local agent instructions |
| `.env.example` | Placeholder PAF configuration keys |
| `.local/` | Ignored private credentials, responses and diagnostics |

To regenerate Word documents from the workshop Markdown and appendices:

```bash
python3 scripts/export_livelab_docx.py
python3 scripts/export_livelab_docx.py --paf-only
```

The exporter uses Python's standard library. When updating the canonical Agent instructions, synchronize both workshops' instruction copies before rebuilding their Word documents. Package validation checks the DOCX structure; it is not visual rendering in Word.

## Legacy implementation

The earlier package-based workflow is documented in the [legacy PL/SQL README](docs/legacy-plsql/README.md), including its account model, functions, provisioning and permission-test assumptions.

## References

- [Oracle Agent Builder components, 26.7](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html)
- [Configure Select AI](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/select-ai.html)
- [Agent Factory database data sources](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html)
- [Configure LLMs](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/llm-management.html)
