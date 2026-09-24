# Build an Oracle Database Monitoring Agent with Private Agent Factory

## Introduction

**Alternative:** for a workshop with the database already prepared, use the [PAF configuration-only LiveLab](../livelab-paf-only/README.md).

In this workshop, build an assistant that answers database monitoring questions and asks for clarification when a request is unclear. Use Oracle Private Agent Factory, Select AI, and five monitoring views in a dedicated application schema.

This is a LiveLabs-style workshop authored from the implementation tested on 24 September 2026. It is a local workshop package, not an officially published Oracle LiveLabs offering. Screens and model availability can vary by release. Agent Factory installation, Autonomous Database provisioning and OCI IAM setup are prerequisites.

**Estimated time:** 90–120 minutes with an existing database and Agent Factory installation; 45–60 minutes if the database views, connection and profile are already prepared.

### Objectives

By the end, you will be able to:

- Connect Agent Factory using `DB_HEALTH_AGENT`.
- Expose monitoring data through five discoverable views.
- Configure an NL2SQL profile through the UI.
- Build an Agent that calls Select AI through a tool connection.
- Handle gibberish, unrelated questions and invalid parameters.
- Test database answers, empty results and unsupported historical requests.

### Workshop path

| Lab | Activity | Time |
|---|---|---|
| 1 | Understand the design and prepare the environment | 10 minutes |
| 2 | Prepare and verify monitoring views | 20 minutes |
| 3 | Configure database and model connections | 15 minutes |
| 4 | Configure the Select AI profile | 15 minutes |
| 5 | Build the monitoring Agent flow | 20 minutes |
| 6 | Validate the Agent in Playground | 20 minutes |
| 7 | Troubleshoot and hand over the MVP | 10 minutes |

**Fast path for the existing project environment:** the views, `ADB HEALTH MVP` connection, `llm_model_entry` model and `DB_HEALTH_AGENT` profile already exist. Check their settings in Labs 2–4, then start Lab 5 with a new flow name. Do not rerun provisioning or overwrite the working flow.

### Files supplied

| File | Purpose |
|---|---|
| [prepare-monitoring.sql](files/prepare-monitoring.sql) | First-time grants and five views; run as ADMIN |
| [verify-monitoring.sql](files/verify-monitoring.sql) | Bounded reads; run as DB_HEALTH_AGENT |
| [monitoring-agent-instructions.txt](files/monitoring-agent-instructions.txt) | Complete tested Agent instructions; paste into the UI |
| [test-prompts.md](files/test-prompts.md) | 24 validation prompts and expected behaviors |

## Lab 1: Understand the design and prepare the environment

### Introduction

The Agent decides whether a request is meaningful and within scope. For valid checks, its Select AI Bridge tool generates and executes a query using the selected database profile. The Agent then explains the returned evidence.

```text
Chat input ───► Agent ───► Chat output
                 ▲
                 │ Tool connection
          Select AI Bridge
          Profile: DB_HEALTH_AGENT
          Action: Run SQL
                 │
                 ▼
          Login: DB_HEALTH_AGENT
          MONITOR_* views
                 │
                 ▼
          Oracle monitoring views
```

The tool connection is attached to the Agent's **Tools** input. The Bridge is not placed between Chat Input and Chat Output as a mandatory processing step.

This workshop follows the Select AI implementation. The earlier `DB_HEALTH_OWNER.DB_HEALTH_API` PL/SQL package is a separate tool path and is not called by this flow. If it exists, leave it intact. `DB_HEALTH_OWNER` remains a schema-only account; Agent Factory logs in as `DB_HEALTH_AGENT`.

### Task 1: Collect the prerequisites

1. Obtain access to an existing Private Agent Factory installation and permission to create workflows, database sources and model configurations.
2. Obtain an Autonomous Database with working Select AI packages. Have a DBA available for the one-time setup.
3. Obtain an ADMIN SQLcl connection and the database's exact `DB_NAME`. ADMIN is used for preparation only.
4. Obtain the runtime `DB_HEALTH_AGENT` login and its password through your approved secret-sharing method.
5. Obtain the wallet/network connection details required by the database. Verify that the Agent Factory host can reach it.
6. Obtain access to an OCI Generative AI model with tool-calling support for the Agent, and a supported model for the Select AI profile. The two configurations are separate.
7. For OCI credential setup, have the approved user OCID, tenancy OCID, API signing-key fingerprint, private PEM key, compartment OCID and model region available in the approved secret store.

Use the deployment URL provided by your facilitator, for example `https://<PAF_HOST>:8080/agentFactory/`. Use a hostname with a valid matching certificate. The sample IP and credentials from an individual installation are not part of this workshop.

### Task 2: Record your lab values

| Item | Workshop value |
|---|---|
| Agent Factory URL | Your facilitator's URL |
| SQLcl ADMIN connection | Your saved connection name |
| Expected database identity | Value of `SYS_CONTEXT('USERENV','DB_NAME')` |
| Runtime database login/schema | `DB_HEALTH_AGENT` |
| Agent Factory database name | `ADB HEALTH MVP` |
| Agent model registration name | `llm_model_entry`, or your equivalent |
| Select AI profile name | `DB_HEALTH_AGENT` |
| New flow name | `ADB Health Monitoring Agent Lab` |

The profile name and database username happen to be identical here, but they are different objects. The database connection selects the login; the Bridge's profile selector selects an AI profile owned by that login.

### Task 3: Understand the data boundary

The tested Select AI path has direct SELECT grants on five SYS source views and cloud-package execution grants. The `MONITOR_*` views present a smaller, easier-to-query column set, but they do not remove the underlying account privileges. `WITH READ ONLY` prevents DML through those views; it does not make every capability of the account read-only.

The Agent's instructions limit its intended behavior. They are not a hard authorization boundary. This MVP also uses an object-list enforcement workaround described in Lab 4. Use the existing fixed PL/SQL API path instead if strict, deterministic function boundaries are required.

The Agent's model receives the question and tool results; the Select AI model receives prompts and schema metadata needed for translation. Private Agent Factory deployment does not itself imply that both models run inside your private network. Use approved model destinations for your data.

**Checkpoint:** you know which account logs in, where model requests go, and which connection/profile names you will use.

## Lab 2: Prepare and verify the monitoring views

### Introduction

A DBA performs this lab once. Participants can skip creation when the five views already exist. The supplied script creates objects in `DB_HEALTH_AGENT`, not ADMIN or SYS.

### Task 1: Verify the target database with SQLcl

1. Open the SQLcl bundled with the Oracle SQL Developer extension. In the project environment it is:

   ```bash
   /home/syazwan/.vscode-server/extensions/oracle.sql-developer-26.2.1-linux-x64/dbtools/sqlcl/bin/sql /nolog
   ```

2. Connect using your saved ADMIN connection:

   ```sql
   connect -name "YOUR_ADMIN_CONNECTION"
   ```

3. Run:

   ```sql
   select sys_context('USERENV','SESSION_USER') as session_user,
          sys_context('USERENV','DB_NAME') as db_name,
          sys_context('USERENV','CON_NAME') as container_name
   from dual;
   ```

4. Confirm that the login is ADMIN and record the intended `DB_NAME` before proceeding.

### Task 2: Provision the account only if it does not exist

If `DB_HEALTH_AGENT` already exists, reuse its approved credential and skip this task. Do not reset its password to make the lab easier.

For a fresh checkout of this project, the facilitator can use the existing provisioning helper from the repository root:

```bash
python3 scripts/db.py preflight --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
python3 scripts/db.py provision --connection 'YOUR_ADMIN_CONNECTION' --expected-db YOUR_DB_NAME
```

This helper creates `DB_HEALTH_AGENT` with `CREATE SESSION`, generates its password privately in `.local/db_health_agent.password`, and also creates the schema-only `DB_HEALTH_OWNER` account used by the project's optional fixed-API design. The owner package itself is not required for this workshop. The helper refuses to adopt existing users or overwrite its credential file.

Read the generated password only through your approved local secret-handling process and use it in connection password fields. Do not add it to lab notes, screenshots or command arguments. Provisioning DDL commits independently; inspect partial state after any failure rather than rerunning blindly.

### Task 3: Create five monitoring views

From the repository root, in the ADMIN SQLcl session, replace `YOUR_DB_NAME` with the exact trusted identifier recorded earlier:

```sql
@docs/livelab/files/prepare-monitoring.sql YOUR_DB_NAME
```

The script:

1. Checks ADMIN and the expected database identity.
2. Checks that `DB_HEALTH_AGENT` exists and the target monitoring objects do not already exist.
3. Grants execution on `DBMS_CLOUD` and `DBMS_CLOUD_AI`.
4. Grants SELECT on `GV_$SESSION`, `GV_$SQLSTATS`, `DBA_TABLESPACE_USAGE_METRICS`, `DBA_TABLESPACES` and `DBA_SCHEDULER_JOB_RUN_DETAILS`.
5. Creates five read-only views with scope comments and reports their validity.

It grants no catalog role, no `SELECT ANY DICTIONARY`, and no permanent `CREATE VIEW` privilege to the runtime login. If objects already exist, it stops instead of replacing them. If setup fails partway through, ask the DBA to inspect the committed changes.

| View in DB_HEALTH_AGENT | What it covers | Key limit |
|---|---|---|
| `MONITOR_DATABASE_OVERVIEW` | Identity and current connection information | Not a health verdict |
| `MONITOR_SESSIONS` | Current active or blocked user sessions | No historical session samples |
| `MONITOR_STORAGE_USAGE` | Tablespace usage and capacity | Not the ADB service storage quota |
| `MONITOR_JOB_RUNS` | Retained Scheduler runs, all statuses | Not job definitions or live running jobs |
| `MONITOR_SQL_WORKLOAD` | Cached cumulative SQL statistics | Not a last-hour/day performance report |

`COLLECTED_AT_UTC` is calculated at query time. It is not a persisted historical sample timestamp. Scheduler `LOG_DATE_UTC` is the timestamp to use for a retained-log time window.

### Task 4: Verify as the runtime user

1. Create or select a SQLcl connection using `DB_HEALTH_AGENT`, the target database's network configuration, and the approved runtime password. Do not copy ADMIN's saved password.
2. Connect as that user and run:

   ```sql
   @docs/livelab/files/verify-monitoring.sql YOUR_DB_NAME
   ```

3. Verify all five views report `VALID` and `READ_ONLY=Y`.
4. Verify the bounded queries execute. An empty sessions/job result is valid when there are no matching records; a permission error is not.

**Checkpoint:** five valid views are readable through an actual `DB_HEALTH_AGENT` login. SQLcl connectivity is only one check; Agent Factory still needs its own connection test.

## Lab 3: Configure database and model connections

### Task 1: Add the database in the UI

1. Sign in to Agent Factory.
2. Open **Data Sources** and choose **Add Data Source → Database**.
3. Enter the name **ADB HEALTH MVP**.
4. Choose the connection method appropriate for the Autonomous Database and provide the required service, wallet and network details.
5. Set **Username** to `DB_HEALTH_AGENT` and enter the runtime password in its password field.
6. Test the connection, then save it. Confirm the source shows as connected.

Use ADMIN only in the preparation session, never as this flow's runtime data source. SQLcl and Agent Factory keep separate saved connections. A passing SQLcl test does not prove the Agent Factory host can reach the database. The documented database-source workflow is in [Oracle's database data-source guide](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html).

### Task 2: Configure the Agent's LLM

1. Open **Settings → LLM Management** (or **LLM Management** in your version).
2. Reuse the approved model registration if one already exists; otherwise create an OCI model connection with your approved credential, region, compartment and model settings.
3. Give it a recognizable name, such as `llm_model_entry`.
4. Test and save the model connection.
5. Confirm that the selected model supports tool calling. The successful database query in Lab 6 is the end-to-end tool-calling test.

The Agent model interprets requests and explains results. The Select AI profile's model generates SQL. A successful test here does not test the database's ability to call its Select AI provider. See [Oracle's LLM configuration guide](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/llm-management.html) for provider-specific fields.

**Checkpoint:** the database connection and the Agent LLM connection both pass their connection tests.

## Lab 4: Configure Select AI through the UI

### Task 1: Open the database's Select AI settings

1. Open **Settings → Select AI Framework**.
2. Select **ADB HEALTH MVP**.
3. Inspect the access/readiness panel. This workshop needs credential/profile management and Select AI execution. It does not use vector indexes or in-database agent teams.
4. If Select AI is unavailable, verify the runtime user and the `DBMS_CLOUD_AI` grant. Do not grant every package merely to make unrelated feature indicators green.

### Task 2: Create or reuse the OCI credential

1. Open **Credentials**.
2. Reuse the approved credential, or choose **Create Credential** and select OCI.
3. Fill in its name, OCI user and tenancy identifiers, signing-key fingerprint and private PEM key using the provider's secure fields.
4. Validate and create the credential.

The credential belongs to the database user selected in the connection. It is separate from the PAF LLM registration. If network setup is required for your provider, the DBA configures the approved destination; runtime ACL-administration access is not required for the flow. Oracle documents a specific OCI Generative AI-on-ADB exception to ACL requirements in [Select AI configuration](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/select-ai.html).

### Task 3: Create the NL2SQL profile

1. Open **Profiles → Create Profile**. If the profile already exists, inspect it instead of creating a duplicate.
2. Use the following values as the workshop configuration:

   | Field | Value |
   |---|---|
   | Profile name | `DB_HEALTH_AGENT` |
   | Provider | OCI |
   | Credential | Approved credential from Task 2 |
   | Region | Approved model region; tested environment used `us-chicago-1` |
   | Compartment | Your approved compartment OCID |
   | Model | Supported model; tested environment used `google.gemini-2.5-flash` |
   | Max tokens | `4096` |
   | Enable NL2SQL | On |
   | Enable RAG | Off |
   | Object list mode | All |

   Model and region availability are deployment-specific; select an available approved model rather than assuming the example identifier is valid everywhere.

3. Under **Select schema owners**, select **DB_HEALTH_AGENT**.
4. Under **DB Tables & Views**, select exactly:

   ```text
   MONITOR_DATABASE_OVERVIEW
   MONITOR_SESSIONS
   MONITOR_STORAGE_USAGE
   MONITOR_JOB_RUNS
   MONITOR_SQL_WORKLOAD
   ```

5. Check **Selected DB tables & views** contains all five objects, with owner `DB_HEALTH_AGENT`.
6. Use `MONITOR_JOB_RUNS`, not the earlier `MONITOR_FAILED_JOBS`, so the same source can answer questions about every retained run status.

### Task 4: Choose the enforcement setting explicitly

Oracle recommends enforcing the object list. Start with **Enforce Object List = On** in a fresh environment and validate actual storage and job execution in Lab 6.

In the tested project environment, storage and job queries failed with `ORA-20004` under enforcement even when generated SQL named the selected wrapper. Direct SQL worked. The exact internal cause was not established. The approved MVP workaround was **Enforce Object List = Off**, and this is the setting used by the working project profile.

To reproduce that environment, set it Off only within the approved workshop scope. The object list then guides metadata selection; it does not restrict execution to those five views. Existing database privileges remain the access boundary. Do not describe the instruction prompt or the view list as enforcing that boundary.

### Task 5: Validate and save

1. Click **Validate Profile**.
2. Resolve any credential, model or permission error.
3. Click **Create Profile** or save the existing profile changes using the available UI control.
4. Refresh the profile list and confirm `DB_HEALTH_AGENT` is available.

**Checkpoint:** profile validation succeeds and the five selected views are visible under `DB_HEALTH_AGENT`. Runtime query execution will be tested separately.

## Lab 5: Build the custom monitoring Agent

### Task 1: Create a new flow

1. Open **Workflows** or **My Custom Flows**.
2. Choose **New Flow** and open Agent Builder.
3. Rename it **ADB Health Monitoring Agent Lab**. Use a distinct name if the working MVP already exists.
4. Enter the description: `Read-only database monitoring with request clarification and evidence-based answers.`

### Task 2: Add the four components

From the component palette, drag these onto the canvas:

| Palette category | Component |
|---|---|
| Inputs | Chat input |
| Agents | Agent |
| Tools | Select AI Bridge |
| Outputs | Chat output |

Arrange Chat Input on the left, Agent in the center, Chat Output on the right, and Select AI Bridge below or beside the Agent.

The tested installed version exposes **Select AI Bridge** under Tools. Some documentation/releases describe **Use as Agent Tool** on the Select AI node. The essential distinction is that the connection must provide a **Tool** to the Agent. A standalone Select AI **Result** connected directly to Chat Output bypasses the request-validation and explanation behavior. See [Agent Builder components](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html) for release-specific node descriptions.

### Task 3: Configure Select AI Bridge

Set these fields:

| Field | Value |
|---|---|
| Mode | Profile |
| Choose database | ADB HEALTH MVP |
| Choose Profile | DB_HEALTH_AGENT |
| Choose AI action | Run SQL |

Refresh a selector if a newly created connection or profile is missing. The action must be **Run SQL** to retrieve database results. **Show SQL** generates SQL text and is useful for diagnosis, but does not execute it.

### Task 4: Configure the Agent

1. In **Select LLM to use**, choose your tested model registration.
2. Set **Temperature** to `0.01`.
3. Set **Agent description** to `Read-only ADB monitoring with clarification and evidence-based answers`.
4. Open [monitoring-agent-instructions.txt](files/monitoring-agent-instructions.txt).
5. Copy the entire file into **Custom instructions**. Do not paste it into the user Prompt field.
6. Leave **Prompt** empty until you connect Chat Input.
7. Leave Sub-agents unused for this workshop.

The supplied instructions define:

- What is in scope and which five views are available.
- How to ask for clarification without guessing limits or durations.
- Why collection timestamps cannot support historical performance comparisons.
- Why no matching failures do not prove job success.
- How to explain empty results and cumulative SQL statistics.
- How to complete slowdown checks and a compact two-call overall-health check.

Do not paste the earlier PL/SQL `GET_*` prompt into this Agent: this flow uses the Select AI Bridge, not the PL/SQL executor.

### Task 5: Connect the ports

Create exactly these three connections:

| From component | Output | To component | Input |
|---|---|---|---|
| Chat input | Message | Agent | Prompt |
| Select AI Bridge | Tool | Agent | Tools |
| Agent | Message | Chat output | Message |

Inspect the endpoint labels before saving. The Agent may also expose an **Agent** output for delegation; use its **Message** output for Chat Output.

### Task 6: Save and disable memory

1. Click **Save**.
2. Open the flow settings/gear and locate **Agent Memory** or **Memory settings**.
3. Set **Enable memory** to Off and save the setting.
4. Reopen settings to confirm it remains Off.
5. Open **Playground**.

Memory settings and current chat history are different concepts. Use a fresh conversation for each independent test so earlier messages do not influence your baseline. For a clarification follow-up, stay in the same conversation.

**Checkpoint:** four components, three connections, the full custom instruction text, the correct Bridge profile/action, and memory disabled.

## Lab 6: Test the Agent in Playground

### Task 1: Prove a real monitoring query works

In a fresh conversation, send:

```text
Show the database identity and service name.
```

Expected: the Agent returns the actual connected database identity and service. If it merely describes how you could query the database, the tool path has not been demonstrated. Inspect execution details or tool traces when your deployment makes them available.

### Task 2: Check the main monitoring features

Run each prompt independently:

| Prompt | Expected result |
|---|---|
| Show tablespaces ordered by usage percentage, highest first. | Percentages in descending order; distinguishes tablespace capacity from service quota |
| Are any sessions blocked? Identify the blocking instance and SID. | Actual current blocking evidence, or a scoped no-matches explanation |
| Show failed job runs in the last 48 hours. | Explicit 48-hour window and retained-log limitation |
| Show the latest 10 job runs of any status. | Recent retained run records without an implicit FAILED filter |
| Show the top five cached SQL entries by cumulative elapsed time. | Five or fewer entries; clearly cumulative |
| Check overall database health. | Identity, sessions/blockers, storage, recent jobs and cumulative workload in a final answer |

Live counts change. There may be no failures or blockers in the lab database. Do not create blocking sessions or failing production jobs solely to produce a more interesting demonstration.

### Task 3: Check everyday wording and unsupported history

| Prompt | Expected behavior |
|---|---|
| The app feels slow today. Can you check the database? | Current sessions and cumulative workload, with limitations; no invented historical evidence |
| My overnight report didn't arrive. Did something fail? | Ask for time window/timezone and job/report identity |
| Was it slower yesterday than today? | Explain that the current/cumulative views cannot answer this comparison |
| Just fix whatever is slowing things down. | Explain read-only scope; offer or perform diagnostics without modification |

For the overnight example, answer the clarification in the same conversation with an actual job name and a clear window, for example `Check the last 12 hours for job <actual_job_name>`. The Agent should apply those parameters explicitly. This follow-up is a workshop exercise, not part of the original independent-prompt regression evidence.

### Task 4: Check gibberish, invalid parameters and scope

| Prompt | Expected behavior |
|---|---|
| asdf qwer zxcv | Ask to rephrase |
| !!! ??? ### | Ask to rephrase |
| banana spaceship database purple | Ask to rephrase, rather than search database names |
| show -5 sessions | Ask for a valid whole-number limit; do not convert to five |
| jobs failed last potato hours | Ask for a valid duration; do not guess 24 hours |
| What is the weather in Kuala Lumpur today? | Explain monitoring-only scope |
| Write me a banana cake recipe. | Explain monitoring-only scope |
| How much revenue did our customers generate last month? | Explain that business data is outside these monitoring sources |
| db slooooowww plzzz chk | Recognize the typo-filled monitoring request and check sessions/workload |
| sessions lockkkkk help??? | Recognize blocking intent and check current blockers |

A clarification response is not by itself proof that no database call occurred. The Bridge may retrieve profile metadata while the graph initializes. Use available tool traces if proving absence of monitoring-query execution is an acceptance requirement.

### Task 5: Record acceptance evidence

Use [test-prompts.md](files/test-prompts.md) for the full 24-case baseline. Record prompt, scope, tool evidence when available, final answer, outcome and observation time. Keep live rows and traces in your private lab workspace.

Use these verdicts:

- **Pass:** correct scope and a supported answer or appropriate clarification.
- **Partial:** useful evidence, but a missing check, limitation or explanation.
- **Fail:** wrong query scope, guessed parameters, invented conclusion, tool error presented as health, or no final answer.

In the implemented environment, all ten targeted clarification/scope cases passed. Initial multi-check completion issues required the final instructions supplied here. Overall health then passed a targeted retest. A complete 24-case run was not repeated after the final overall-health-only adjustment. Re-run the full suite in your own environment; do not assume the same model will produce identical answers. The original evidence is in the [implementation test report](../../tests/paf/results-monitoring-agent-2026-09-24.md).

**Checkpoint:** the Agent handles valid monitoring questions, malformed requests and unrelated questions with the intended behavior; outstanding partial/fail cases are recorded.

## Lab 7: Troubleshoot and hand over the MVP

### Task 1: Use the symptom table

| Symptom | Check and action |
|---|---|
| No tables/views in the profile picker | Confirm the connection logs in as DB_HEALTH_AGENT, select that owner, refresh/reopen the picker, and verify the five views are VALID and readable |
| Cannot find system views under SYS | The tested picker omitted SYS or dynamic performance views; use the supplied same-schema MONITOR_* views. A synonym alone was not validated as a solution |
| Selected DB_HEALTH_OWNER but picker is empty | That schema owns the optional package; these workshop views are in DB_HEALTH_AGENT |
| Select AI Bridge profile list is empty | Verify the selected database, owning user, saved profile and grants, then refresh |
| Profile validation passes but execution fails | Check provider access from the database and try a real Run SQL request; profile validation is not end-to-end execution |
| SQL text appears instead of database results | Bridge is probably set to Show SQL; set Run SQL |
| ORA-20000 mentions max_tokens=1024 | Increase the Select AI profile Max Tokens to 4096, save, and retry. This does not correct SQL semantics |
| ORA-20004 object-list rejection | Compare generated fully-qualified object names with the saved list and test the exact SQL as DB_HEALTH_AGENT. Review the documented enforcement workaround rather than guessing that the name is the cause |
| Gibberish returns monitoring data | Check that Chat Input feeds Agent Prompt, that full instructions are saved, and that the Bridge is connected as a Tool; use a fresh chat |
| Empty output is shown as [] | Verify Agent Message feeds Chat Output and instructions require an explanation of empty results |
| Answer promises more checks but stops | Use the supplied completion rules and inspect actual tool calls; the promise does not mean work continues in the background |
| Overall health finishes without an answer | Use the supplied two-call strategy. It fixed the observed case, but the internal runtime cause was not proven |
| Yesterday was allegedly faster/slower | Check for misuse of COLLECTED_AT_UTC or missing values treated as zero/NO. These views cannot establish historical performance |

### Task 2: Isolate SQL generation from execution when necessary

As `DB_HEALTH_AGENT` in SQLcl:

```sql
exec dbms_cloud_ai.set_profile('DB_HEALTH_AGENT');
select ai showsql Show tablespaces ordered by usage percentage, highest first;
```

ShowSQL invokes the configured provider but does not execute the generated SELECT. Inspect it before running any diagnostic SQL. A fresh ShowSQL result may differ from the SQL generated for an earlier failed request; label it as a reproduction.

To inspect saved nonsecret profile settings:

```sql
select attribute_name, attribute_value
from user_cloud_ai_profile_attributes
where profile_name = 'DB_HEALTH_AGENT'
  and attribute_name in ('object_list', 'object_list_mode',
                         'enforce_object_list', 'max_tokens')
order by attribute_name;
```

Avoid exporting credentials or entire connection records into the report. A successful direct SQL query establishes database readability, not correctness of the model-generated query or Agent answer.

### Task 3: Save and hand over

1. Save the working flow and its final instructions.
2. Record the database source, profile, Agent model, memory setting, test date and unresolved issues.
3. If the workshop includes publication, use **Publish** after the acceptance review. Publishing is unnecessary just to author and test in Playground in the tested deployment.
4. If an integration is required, use the flow's Integration UI and its generated authentication instructions. Do not reuse another flow's API key or paste keys into this lab.
5. Keep the distinction between a tested MVP and enforced production controls in the handover: instructions are probabilistic, generated SQL still needs semantic checks, and historical monitoring requires a historical data source.

### Task 4: End the workshop

For a shared workshop, leave the common database/profile resources intact. Remove only the participant's uniquely named flow if the facilitator requests it. Do not drop DB_HEALTH_AGENT, revoke shared grants, or delete profiles used by other flows. No automatic destructive cleanup script is supplied.

## Learn more

- [Oracle Agent Builder components](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html)
- [Configure Select AI](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/select-ai.html)
- [Database data sources](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html)
- [Configure LLMs](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/llm-management.html)
- [Project flow setup](../monitoring-agent-flow.md)
- [Failure investigation](../../tests/paf/select-ai-failed-case-investigation-2026-09-24.md)

## Acknowledgements

- Workshop basis: the database monitoring MVP and its saved validation evidence in this repository.
- Last updated: September 2026.
