# Build a Database Monitoring Agent — PAF Configuration Only

## Introduction

Configure a database monitoring assistant entirely through Oracle Private Agent Factory (PAF). The database is prepared before the workshop. Participants configure connections, create or reuse a Select AI profile, build an Agent workflow and validate its answers in Playground.

**Estimated time:** 60–75 minutes. Allow additional time for the optional full 24-prompt regression.

**Audience:** agent builders and workshop participants with access to an installed PAF environment.

This alternative LiveLabs-style guide is based on the tested monitoring MVP. It is a local workshop document, not an officially published Oracle LiveLabs offering. UI labels can vary by release; the tested installation exposes the native **Select AI Bridge** component.

### Objectives

- Configure the prepared database as a PAF data source.
- Select a tool-capable Agent model.
- Configure an NL2SQL profile using the prepared monitoring views.
- Connect an Agent to Select AI Bridge.
- Test valid monitoring requests, gibberish and out-of-scope questions.

### Workshop agenda

| Lab | Activity | Time |
|---|---|---|
| 1 | Confirm the prepared environment | 5 minutes |
| 2 | Configure the PAF database connection | 10 minutes |
| 3 | Configure the Agent model | 10 minutes |
| 4 | Configure the Select AI profile | 15 minutes |
| 5 | Build the custom Agent flow | 15 minutes |
| 6 | Test the flow in Playground | 15 minutes |
| 7 | Save, troubleshoot and hand over | 5 minutes |

### Included files

- [Complete Agent instructions](files/monitoring-agent-instructions.txt) — paste into the Agent Custom instructions field; Appendix A in Word.
- [24 validation prompts](files/test-prompts.md) — test cases and expected behavior; Appendix B in Word.

## Lab 1: Confirm the prepared environment

### Task 1: Check the facilitator handoff

Before participants begin, the facilitator has prepared:

- An installed, reachable PAF instance and participant login with workflow, data-source and model-configuration permissions.
- An Autonomous Database reachable from PAF.
- The runtime database login `DB_HEALTH_AGENT`, its credential and any required wallet/service details.
- Required database permissions and Select AI packages.
- Five valid, readable monitoring views in the `DB_HEALTH_AGENT` schema, listed below.
- Approved access to the model provider from both PAF and the database.
- An existing approved model registration/Select AI credential, or the provider details needed to configure these through PAF.
- The approved object-list enforcement setting for the workshop.

This lab contains no database provisioning, user creation, grants, view creation, SQLcl tasks or database setup scripts. If a prerequisite is missing, the facilitator repairs the prepared environment before the participant continues.

### Task 2: Record the values you will use

| Item | Value |
|---|---|
| PAF URL | Facilitator-provided HTTPS URL |
| PAF participant login | Your assigned account |
| Database source display name | `ADB HEALTH MVP` |
| Database username/schema | `DB_HEALTH_AGENT` |
| Agent LLM registration | `llm_model_entry`, or the supplied equivalent |
| Select AI profile | `DB_HEALTH_AGENT`, or a unique participant profile name |
| New flow | `ADB Health Monitoring Agent Lab - <your-name>` |
| Select AI provider credential | Facilitator-provided credential name, or approved details for UI creation |

Use credentials only in the appropriate password/key fields. Do not include them in prompts, screenshots or lab notes. For shared resources, reuse the prepared connection/profile without editing it; create a uniquely named profile when the facilitator assigns individual configuration work.

### Task 3: Understand the available monitoring data

| View | Available evidence | Limitation |
|---|---|---|
| MONITOR_DATABASE_OVERVIEW | Database identity and service | Does not establish overall health |
| MONITOR_SESSIONS | Current active or blocked user sessions | No historical session samples |
| MONITOR_STORAGE_USAGE | Tablespace used percentage and capacity | Not the Autonomous service storage quota |
| MONITOR_JOB_RUNS | Retained Scheduler runs, all statuses | Not job definitions or a live running-job inventory |
| MONITOR_SQL_WORKLOAD | Cached cumulative SQL counters | Not a yesterday/today performance history |

`COLLECTED_AT_UTC` is the current observation time, not a stored performance-history timestamp. Only the job-run view contains retained event history for time-window questions.

### Task 4: Review the flow you will build

```text
Chat input ─────► Agent ─────► Chat output
                   ▲
                   │ Tool
            Select AI Bridge
            Profile + Run SQL
                   │
                   ▼
       Prepared MONITOR_* views
```

The Agent interprets requests and explains tool results. Select AI translates a validated monitoring request into a database query. The PAF Agent model and the Select AI profile model are separate configurations; use the destinations approved for your environment.

**Checkpoint:** the participant has all handoff values and understands the monitoring scope.

## Lab 2: Configure the PAF database connection

### Task 1: Open the database sources

1. Sign in to PAF using the facilitator-provided URL.
2. Open **Data Sources**.
3. Look for **ADB HEALTH MVP**.
4. If the prepared connection already exists and is available to you, open it, confirm its identity and test it. Skip creating a duplicate.

### Task 2: Add the connection if it is not registered yet

1. Choose **Add Data Source → Database**.
2. Enter **ADB HEALTH MVP**, or your assigned unique display name.
3. Choose the connection type specified by the facilitator.
4. Enter the supplied service/network details and upload or select the supplied wallet if that connection method requires it.
5. Set the database username to **DB_HEALTH_AGENT**.
6. Enter the runtime password in the password field.
7. Click the connection-test control.
8. Save the source and confirm its connected status.

Use the prepared runtime login. ADMIN is not the database identity for this Agent. Do not use `DB_HEALTH_OWNER`: it belongs to the project's separate package-based implementation and is not the view owner used by this lab.

### Task 3: Handle a failed connection

Record the error and ask the facilitator to check the supplied credential, service/wallet details and network reachability from the PAF host. Successful connectivity from another machine does not establish PAF connectivity.

**Checkpoint:** PAF's database connection test passes using `DB_HEALTH_AGENT`.

## Lab 3: Configure the Agent model

### Task 1: Select or register the model

1. Open **Settings → LLM Management**, or **LLM Management** in your release.
2. Find the supplied model registration, such as **llm_model_entry**.
3. If it exists, confirm it is the facilitator-approved tool-capable model and run the available connection test.
4. If registration is part of your assignment, choose the add/create control and select the supplied provider, such as OCI.
5. Enter the approved region, model identifier, compartment and authentication details required by that provider.
6. Give the registration a recognizable name and save it.
7. Run the available model test and resolve any error before proceeding.

A model must support tool calling to use the Bridge through the Agent. The real monitoring request in Lab 6 will test this capability end to end.

### Task 2: Distinguish the two model configurations

| Configuration | Purpose | Configured where |
|---|---|---|
| Agent model | Interpret the user request, decide whether to call a tool, explain results | PAF LLM Management |
| Select AI profile model | Translate the monitoring request into a database query | PAF Select AI Framework profile |

A passing Agent-model connection test does not prove that the database can reach its Select AI provider. PAF can use a hosted model even when the application itself is privately deployed; use the approved provider destination.

**Checkpoint:** the Agent model is registered, available to your account and passes its connection test.

## Lab 4: Configure the Select AI profile

### Task 1: Open the prepared database

1. Open **Settings → Select AI Framework**.
2. Select **ADB HEALTH MVP** or your assigned database source.
3. Confirm that credential/profile management and Select AI are available.
4. If the required feature is missing, give the error to the facilitator. Do not run grant statements or alter the database as part of this lab.

Vector indexes, RAG and in-database teams are not used in this workflow. Their readiness indicators do not need to be enabled for this exercise.

### Task 2: Reuse or create the provider credential through PAF

1. Open **Credentials** and look for the credential supplied for the lab.
2. Reuse it if it already exists.
3. If credential creation is assigned, choose **Create Credential** and select the approved provider.
4. For OCI, enter the approved credential name, user OCID, tenancy OCID, API signing-key fingerprint and private PEM key in the provider form.
5. Validate and create the credential.

The facilitator has already prepared provider access and IAM/network prerequisites. If validation fails, stop at this checkpoint and request environment assistance; do not change database ACLs or permissions.

### Task 3: Create or inspect the profile

1. Open **Profiles**.
2. If using a shared, prepared **DB_HEALTH_AGENT** profile, inspect its settings without changing it.
3. Otherwise choose **Create Profile** and use the name assigned to your participant, for example **DB_HEALTH_AGENT_LAB_A**.
4. Fill in the profile settings:

   | Field | Value |
   |---|---|
   | Provider | Facilitator-approved provider; tested setup used OCI |
   | Credential | Approved credential from Task 2 |
   | Region | Supplied region; tested setup used `us-chicago-1` |
   | Compartment | Supplied compartment OCID |
   | Model | Supplied supported model; tested setup used `google.gemini-2.5-flash` |
   | Max tokens | `4096` |
   | Enable NL2SQL | On |
   | Enable RAG | Off |
   | Object list mode | All |

Use a model available in your approved region. The example identifiers describe the tested implementation, not a promise of availability in every tenancy.

### Task 4: Select the prepared views

1. Under **Select schema owners**, choose **DB_HEALTH_AGENT**.
2. Under **DB Tables & Views**, select:

   ```text
   MONITOR_DATABASE_OVERVIEW
   MONITOR_SESSIONS
   MONITOR_STORAGE_USAGE
   MONITOR_JOB_RUNS
   MONITOR_SQL_WORKLOAD
   ```

3. Check that **Selected DB tables & views** contains exactly these five objects.
4. Confirm that every object's owner is **DB_HEALTH_AGENT**, even when you gave the profile a different name.
5. Use **MONITOR_JOB_RUNS** for all retained statuses, rather than the earlier failed-only view.

If the picker is empty, verify the selected source and owner, then refresh or reopen the form. If the five views remain absent, ask the facilitator to repair the prepared environment. Participants do not create views or synonyms in this workshop.

### Task 5: Confirm object-list enforcement

Use the facilitator's approved **Enforce Object List** setting. Do not change a shared profile to fix an individual test.

The working project MVP used **Off** after enforcement caused `ORA-20004` for certain monitoring queries. This is a documented workaround with an unresolved internal cause, not a universal Select AI requirement. Other environments can retain enforcement when their tests pass.

With enforcement Off, the selected list guides SQL-generation metadata but does not limit execution to those views. Existing database permissions remain the access boundary. The Agent's scope instructions improve behavior but do not replace that boundary.

### Task 6: Validate and save

1. Click **Validate Profile**.
2. Resolve any configuration error using the supplied provider values or facilitator assistance.
3. Create/save your assigned profile if this is a new one.
4. Confirm the profile appears in the selected database's profile list.
5. Record the exact profile name for the Bridge in Lab 5.

**Checkpoint:** the profile validates, references the five prepared views, and is available under the intended database connection.

## Lab 5: Build the custom Agent flow

### Task 1: Create your flow

1. Open **Workflows** or **My Custom Flows**.
2. Choose **New Flow** to open Agent Builder.
3. Rename the flow **ADB Health Monitoring Agent Lab - <your-name>**.
4. Set its description to **Read-only monitoring with clarification and evidence-based answers**.

### Task 2: Add four components

| Palette category | Component |
|---|---|
| Inputs | Chat input |
| Agents | Agent |
| Tools | Select AI Bridge |
| Outputs | Chat output |

Place Chat Input on the left, Agent in the center and Chat Output on the right. Place Select AI Bridge below the Agent.

The tested version uses **Select AI Bridge**. Some releases describe **Use as Agent Tool** on the Select AI component. Use the variant that exposes a **Tool** output for the Agent. Sending a standalone Select AI Result directly to Chat Output bypasses the Agent's request clarification and result explanation.

### Task 3: Configure the Bridge

| Field | Setting |
|---|---|
| Mode | Profile |
| Choose database | ADB HEALTH MVP, or your assigned source |
| Choose Profile | The exact profile name recorded in Lab 4 |
| Choose AI action | Run SQL |

Refresh the database/profile selectors if needed. **Run SQL** retrieves query results. **Show SQL** only generates SQL text and is not the action for the finished monitoring flow.

### Task 4: Configure the Agent

1. Select the tool-capable model registration from Lab 3.
2. Set **Temperature** to `0.01`.
3. Set **Agent description** to **Read-only ADB monitoring with clarification and evidence-based answers**.
4. Open [Complete Agent instructions](files/monitoring-agent-instructions.txt), provided as Appendix A in the Word document.
5. Copy the complete text into **Custom instructions**.
6. Leave the user **Prompt** field empty until Chat Input is connected.
7. Leave Sub-agents unused.

The instructions cover gibberish, unrelated requests, invalid parameters, current versus historical data, empty results and final-answer completion. They also prescribe a compact two-call overall-health check, which completed successfully in the targeted implementation retest.

The same prompt works with an individually named profile because the Bridge supplies that configuration. The monitoring schema/view names remain `DB_HEALTH_AGENT.MONITOR_*`.

### Task 5: Wire the components

Create exactly these connections:

| From | Output port | To | Input port |
|---|---|---|---|
| Chat input | Message | Agent | Prompt |
| Select AI Bridge | Tool | Agent | Tools |
| Agent | Message | Chat output | Message |

Use the Agent's **Message** output, not its separate **Agent** delegation output. There should be no direct Chat Input-to-Bridge or Bridge-to-Chat Output connection in this flow.

### Task 6: Save and disable memory

1. Click **Save**.
2. Open the flow's settings/gear and locate **Agent Memory** or **Memory settings**.
3. Set **Enable memory** to Off and save it.
4. Reopen the setting to confirm it is Off.
5. Open **Playground**.

Memory and current conversation history are different. Start a fresh conversation for independent tests; keep the same conversation when answering a clarification question.

**Checkpoint:** four components, three connections, the full instructions, the selected profile with Run SQL, and memory disabled.

## Lab 6: Test the flow in Playground

### Task 1: Validate database access

Send this in a fresh conversation:

```text
Show the database identity and service name.
```

Expected: actual connected database identity and service information. A general explanation of how to query identity is not a completed database check. Inspect available tool execution details when provided by your PAF deployment.

### Task 2: Validate monitoring behavior

| Prompt | Expected behavior |
|---|---|
| Show tablespaces ordered by usage percentage, highest first. | Descending usage order and tablespace-versus-service-capacity distinction |
| Are any sessions blocked? Identify the blocking instance and SID. | Current blockers or a scoped no-matching-blockers explanation |
| Show failed job runs in the last 48 hours. | Uses the requested window and explains retained-log coverage |
| Show the latest 10 job runs of any status. | Latest retained runs without restricting them to failures |
| Show the top five cached SQL entries by cumulative elapsed time. | Cumulative workload rankings, not a historical daily report |
| Check overall database health. | Final answer covering identity, sessions/blockers, storage, recent jobs and cumulative workload |

No matching failed jobs or blockers may be the correct result. Do not compare your live counts with fixed example numbers or create database incidents to populate the demonstration.

### Task 3: Validate clarification and scope

| Prompt | Expected behavior |
|---|---|
| asdf qwer zxcv | Ask the user to rephrase |
| !!! ??? ### | Ask for a meaningful monitoring question |
| banana spaceship database purple | Clarify rather than invent a database search |
| show -5 sessions | Ask for a valid limit instead of silently converting to five |
| jobs failed last potato hours | Ask for a valid duration instead of guessing 24 hours |
| My overnight report didn't arrive. Did something fail? | Clarify window/timezone and report/job identity |
| Was it slower yesterday than today? | Explain that current/cumulative views cannot establish this comparison |
| What is the weather in Kuala Lumpur today? | Explain monitoring-only scope |
| Write me a banana cake recipe. | Explain monitoring-only scope |
| How much revenue did our customers generate last month? | Explain that these views do not contain business/revenue data |

The intended behavior is to avoid monitoring queries for invalid or unrelated requests. A final clarification answer alone does not prove that no tool was invoked. The Bridge may also read profile metadata while initializing. Use traces if your acceptance criteria require verifying tool-call absence.

### Task 4: Check understandable typos and everyday requests

| Prompt | Expected behavior |
|---|---|
| db slooooowww plzzz chk | Recognize monitoring intent and check sessions plus workload |
| sessions lockkkkk help??? | Recognize blocking intent |
| The app feels slow today. Can you check the database? | Complete current-session and cumulative-workload checks with limitations |
| Just fix whatever is slowing things down. | Explain read-only scope; offer or perform diagnostics without claiming a fix |

An answer ending with **I will now check...** is incomplete unless those checks actually run and a final answer follows. The supplied completion instructions address this observed issue.

### Task 5: Record the outcome

Use [24 validation prompts](files/test-prompts.md), included as Appendix B, for the optional complete regression.

| Verdict | Meaning |
|---|---|
| Pass | Correctly scoped, evidence-supported answer or appropriate clarification |
| Partial | Useful answer with missing evidence, scope or explanation |
| Fail | Wrong scope, guessed parameters, invented conclusion, unhandled failure or missing final answer |

Record the prompt, date/time, answer and verdict in your private workshop notes. A successful response or HTTP status does not establish semantic correctness.

The implementation's ten clarification/scope cases passed, and overall health passed after a targeted instruction adjustment. The full 24-case suite was not repeated after that last adjustment. These are reference results, not a guarantee for your model or environment; validate your own flow.

**Checkpoint:** valid monitoring queries work and malformed/unrelated requests receive the intended response. Any unresolved partial/fail cases are recorded.

## Lab 7: Save, troubleshoot and hand over

### Task 1: Troubleshoot from PAF

| Symptom | Participant action |
|---|---|
| Database connection fails | Recheck supplied connection fields; ask the facilitator to inspect prepared connectivity/credentials |
| Required Select AI access is missing | Escalate to the facilitator; database grants are outside this lab |
| Schema picker is empty | Select DB_HEALTH_AGENT, confirm the source and refresh; ask the facilitator if views remain absent |
| Profile missing from Bridge | Confirm database selection and exact saved profile name; refresh the selector |
| Output contains SQL instead of results | Set Bridge action to Run SQL |
| Token-limit error mentions 1024 | Check that your assigned profile uses Max Tokens 4096; do not edit a shared profile without facilitator coordination |
| ORA-20004 object-list error | Capture the profile/action and message; have the facilitator review the agreed enforcement configuration |
| Gibberish returns database information | Check Agent instructions and the three port connections; start a fresh chat |
| Empty result shown as [] | Ensure Agent Message reaches Chat Output and the instructions require explanation |
| Overall health produces no final answer | Confirm the full prompt includes the two-call completion strategy; inspect execution details and report any remaining failure |
| Historical answer gives a confident YES/NO | Treat as a failed test; current collection timestamps are not performance history |

Do not add database privileges, create synonyms or alter the prepared views to work around UI errors during this workshop.

### Task 2: Save the finished configuration

1. Save the flow and check its final component connections.
2. Record the database source, model registration, Select AI profile, memory setting and test outcomes.
3. If your workshop includes publication, click **Publish** after the facilitator's acceptance review.
4. For external integration, use the flow's Integration UI and its generated instructions as a separate exercise. No API keys are required for this Playground lab.
5. Leave shared data sources, credentials, profiles and database resources intact. Remove only your uniquely named participant flow if asked by the facilitator.

**Completion:** you have configured a database monitoring Agent through PAF, using the prepared database and validated UI behavior. Instruction-based controls improve the MVP's responses but are not deterministic enforcement of database access or SQL semantics.

## Reference material

- [Agent Builder components](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html)
- [Select AI configuration](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/select-ai.html)
- [Database data sources](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html)
- [LLM configuration](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/llm-management.html)

Last updated: September 2026. This PAF-only alternative intentionally assumes all database preparation has been completed by the facilitator.
