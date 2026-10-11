# Build a Database Monitoring Agent — PAF Configuration Only

## Introduction

Configure a database monitoring assistant entirely through Oracle Private Agent Factory (PAF). The database is prepared before the workshop. Participants configure connections, create or reuse a Select AI profile, build an Agent workflow and validate its answers in Playground.

**Estimated time:** 60–75 minutes, plus 25–30 minutes for optional MCP Lab 8. Allow additional time for the optional 24-question exercise in Appendix B.

**Audience:** agent builders and workshop participants with access to an installed PAF environment.

This workshop uses the native **Select AI Bridge** component. UI labels may vary
by release. It is a local workshop guide, not an officially published Oracle LiveLabs offering.

### Objectives

- Configure the prepared database as a PAF data source.
- Select a tool-capable Agent model.
- Configure an NL2SQL profile using the prepared monitoring views.
- Connect an Agent to Select AI Bridge.
- Test valid monitoring requests, gibberish and out-of-scope questions.
- Build a separate AI-led DBA login troubleshooting demo using read-only ADB MCP tools, without a required runbook.

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
| 8 (optional) | Add AI-led DBA troubleshooting with MCP | 25–30 minutes |

### Included files

- [Complete Agent instructions](files/monitoring-agent-instructions.txt) — paste into the Agent Custom instructions field; Appendix A in Word.
- [24 validation prompts](files/test-prompts.md) — test cases and expected behavior; Appendix B in Word.
- [MCP demo Agent instructions](../livelab-mcp/files/agent-instructions.txt) — complete instructions for the separate MCP Agent; Appendix C in Word.
- [MCP validation prompts](files/mcp-test-prompts.md) — 15 normal, nontechnical, gibberish, timezone and safety checks; Appendix D in Word.

### Using the screenshots

Use the screenshots to locate fields and check your configuration. Labels may
vary by PAF release. Grey masks hide credentials, identifiers and database answers;
compare your own results with each task's expected behavior. If your connection
test shows an error, ask the facilitator for help before continuing.

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

![Lab 1, Task 1 — Signed-in PAF home and the available configuration areas; the facilitator handoff is an offline checklist.](images/lab01-01-home.png)

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

![Lab 1, Task 2 — Inspect the source name, connected status and runtime username; obtain private values from the facilitator.](images/lab02-03-source-details.png)

### Task 3: Understand the available monitoring data

| View | Available evidence | Limitation |
|---|---|---|
| MONITOR_DATABASE_OVERVIEW | Database identity and service | Does not establish overall health |
| MONITOR_SESSIONS | Current active or blocked user sessions | No historical session samples |
| MONITOR_STORAGE_USAGE | Tablespace used percentage and capacity | Not the Autonomous service storage quota |
| MONITOR_JOB_RUNS | Retained Scheduler runs, all statuses | Not job definitions or a live running-job inventory |
| MONITOR_SQL_WORKLOAD | Cached cumulative SQL counters | Not a yesterday/today performance history |

`COLLECTED_AT_UTC` is the current observation time, not a stored performance-history timestamp. Only the job-run view contains retained event history for time-window questions.

![Lab 1, Task 3 — The five prepared views selected in the actual profile.](images/lab04-07-five-views.png)

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

![Lab 1, Task 4 — Reference view of the completed four-component flow and its three connections.](images/lab05-13-wire-output.png)

## Lab 2: Configure the PAF database connection

### Task 1: Open the database sources

1. Sign in to PAF using the facilitator-provided URL.
2. Open **Data Sources**.
3. Look for **ADB HEALTH MVP**.
4. If the prepared connection already exists and is available to you, open it, confirm its identity and test it. Skip creating a duplicate.

![Lab 2, Task 1, step 1 — PAF sign-in screen before entering credentials.](images/lab02-01-sign-in.png)

![Lab 2, Task 1, steps 2–4 — Open Data Sources and locate the connected ADB HEALTH MVP source.](images/lab02-02-data-sources.png)

Use the eye icon in the source's **Actions** column to inspect its details. This release's details dialog displays connection status but does not expose a separate test button; **Test connection** is available in the add-source form.

![Lab 2, Task 1, step 4 — Inspect the existing connection without registering a duplicate.](images/lab02-03-source-details.png)

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

![Lab 2, Task 2, steps 1–8 — Optional Basic connection form, including Test connection and Add database source. This empty form was not submitted.](images/lab02-04-add-database-basic.png)

![Lab 2, Task 2, steps 3–6 — Optional Wallet connection form; use only the facilitator-provided wallet and DB_HEALTH_AGENT login.](images/lab02-05-add-database-wallet.png)

### Task 3: Handle a failed connection

Record the error and ask the facilitator to check the supplied credential, service/wallet details and network reachability from the PAF host. Successful connectivity from another machine does not establish PAF connectivity.

Use **Test connection** from Task 2. If it fails, share the error with the facilitator.

**Checkpoint:** PAF's database connection test passes using `DB_HEALTH_AGENT`.

## Lab 3: Configure the Agent model

### Task 1: Select or register the model

1. Open **Settings → Model Management** in the captured release; other releases use **LLM Management**.
2. Find the supplied model registration, such as **llm_model_entry**.
3. If it exists, confirm it is the facilitator-approved tool-capable model and run the available connection test.
4. If registration is part of your assignment, choose the add/create control and select the supplied provider, such as OCI.
5. Enter the approved region, model identifier, compartment and authentication details required by that provider.
6. Give the registration a recognizable name and save it.
7. Run the available model test and resolve any error before proceeding.

A model must support tool calling to use the Bridge through the Agent. The real monitoring request in Lab 6 will test this capability end to end.

![Lab 3, Task 1, steps 1–3 — Generative model registration llm_model_entry under Model Management.](images/lab03-01-model-management.png)

![Lab 3, Task 1, steps 4–6 — Optional Add configuration form for the Agent model; no new model was registered.](images/lab03-02-add-model.png)

![Lab 3, Task 1, step 3 — The existing registration's actions include View details and Test connection.](images/lab03-03-model-actions.png)

![Lab 3, Task 1, step 3 — Inspect the existing model's provider, status and access details.](images/lab03-04-model-details.png)

![Lab 3, Task 1, step 7 — Actual connection-test failure: Missing field: user. This is not a passing checkpoint.](images/lab03-05-model-test.png)

### Task 2: Distinguish the two model configurations

| Configuration | Purpose | Configured where |
|---|---|---|
| Agent model | Interpret the user request, decide whether to call a tool, explain results | PAF Model Management / LLM Management |
| Select AI profile model | Translate the monitoring request into a database query | PAF Select AI Framework profile |

A passing Agent-model connection test does not prove that the database can reach its Select AI provider. PAF can use a hosted model even when the application itself is privately deployed; use the approved provider destination.

Compare the Agent registration screenshot above with the separate **Provider & Model configuration** screenshot in Lab 4, Task 3. These are different model configurations; this comparison has no additional UI action.

**Checkpoint:** the Agent model is registered, available to your account and passes its connection test.

## Lab 4: Configure the Select AI profile

### Task 1: Open the prepared database

1. Open **Settings → Select AI Framework**.
2. Select **ADB HEALTH MVP** or your assigned database source.
3. Confirm that credential/profile management and Select AI are available.
4. If the required feature is missing, give the error to the facilitator. Do not run grant statements or alter the database as part of this lab.

Vector indexes, RAG and in-database teams are not used in this workflow. Their readiness indicators do not need to be enabled for this exercise.

![Lab 4, Task 1, steps 1–4 — Select AI Framework with ADB HEALTH MVP selected and its package-access status. Network ACL Admin is shown by default; this lab makes no ACL changes.](images/lab04-01-select-ai-readiness.png)

### Task 2: Reuse or create the provider credential through PAF

1. Open **Credentials** and look for the credential supplied for the lab.
2. Reuse it if it already exists.
3. If credential creation is assigned, choose **Create Credential** and select the approved provider.
4. For OCI, enter the approved credential name, user OCID, tenancy OCID, API signing-key fingerprint and private PEM key in the provider form.
5. Validate and create the credential.

The facilitator has already prepared provider access and IAM/network prerequisites. If validation fails, stop at this checkpoint and request environment assistance; do not change database ACLs or permissions.

![Lab 4, Task 2, steps 1–2 — Reuse the prepared OCI_GEN_AI credential; its user OCID is masked.](images/lab04-02-credentials.png)

![Lab 4, Task 2, steps 3–5 — Optional credential-creation form with PEM upload, Validate credential and Create credential controls; not submitted.](images/lab04-03-create-credential.png)

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

![Lab 4, Task 3, steps 1–3 — The saved DB_HEALTH_AGENT profile; use its edit icon to inspect settings, or Create profile for an assigned individual profile.](images/lab04-04-profiles.png)

![Lab 4, Task 3, step 4 — Provider, credential, model and region configuration in the existing profile.](images/lab04-05-profile-settings.png)

![Lab 4, Task 3, step 4 — Tuning and feature controls, including Max tokens, NL2SQL and RAG.](images/lab04-06-tokens-nl2sql.png)

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

![Lab 4, Task 4, step 1 — Choose DB_HEALTH_AGENT as the schema owner and allow the object picker to finish loading.](images/lab04-10-schema-picker.png)

![Lab 4, Task 4, steps 2–5 — Exactly five views selected. MONITOR_FAILED_JOBS remains unselected; use MONITOR_JOB_RUNS.](images/lab04-07-five-views.png)

### Task 5: Confirm object-list enforcement

Use the facilitator's approved **Enforce Object List** setting. Do not change a shared profile to fix an individual test.

Use the facilitator-assigned enforcement setting. If a query returns `ORA-20004`,
ask the facilitator to review the profile; do not change a shared setting yourself.

With enforcement Off, the selected list guides SQL-generation metadata but does not limit execution to those views. Existing database permissions remain the access boundary. The Agent's scope instructions improve behavior but do not replace that boundary.

![Lab 4, Task 5 — Existing approved enforcement setting and object-list mode; inspected without changing the shared profile.](images/lab04-08-object-enforcement.png)

### Task 6: Validate and save

1. Click **Validate Profile**, or **Validate changes** when inspecting an existing profile in this release.
2. Resolve any configuration error using the supplied provider values or facilitator assistance.
3. Create/save your assigned profile if this is a new one.
4. Confirm the profile appears in the selected database's profile list.
5. Record the exact profile name for the Bridge in Lab 5.

**Checkpoint:** the profile validates, references the five prepared views, and is available under the intended database connection.

![Lab 4, Task 6, steps 1–2 — Actual successful validation of the existing Select AI profile.](images/lab04-09-profile-validates.png)

For steps 3–5, a new profile is saved using **Create/Save profile**; for this shared profile, close with **Cancel** after inspection. The saved-profile list in Task 3 is the reference for confirming its name and availability.

## Lab 5: Build the custom Agent flow

### Task 1: Create your flow

1. Open **Workflows** or **My Custom Flows**.
2. Choose **Create flow** (or **New Flow**) to open Agent Builder.
3. In this release, add the first component from Task 2 to create an untitled draft. Click the pencil beside its name and rename it **ADB Health Monitoring Agent Lab - <your-name>**.
4. Set its description to **Read-only monitoring with clarification and evidence-based answers**, then click **Save changes**.

![Lab 5, Task 1, steps 1–2 — My Custom Flows and the Create flow control.](images/lab05-01-custom-flows.png)

![Lab 5, Task 1, step 2 — Empty Agent Builder canvas and component palette.](images/lab05-02-new-flow.png)

![Lab 5, Task 1, steps 3–4 — Name and describe the automatically created draft using Edit details.](images/lab05-03-name-flow.png)

### Task 2: Add four components

| Palette category | Component |
|---|---|
| Inputs | Chat input |
| Agents | Agent |
| Tools | Select AI Bridge |
| Outputs | Chat output |

Place Chat Input on the left, Agent in the center and Chat Output on the right. Place Select AI Bridge below the Agent.

The tested version uses **Select AI Bridge**. Some releases describe **Use as Agent Tool** on the Select AI component. Use the variant that exposes a **Tool** output for the Agent. Sending a standalone Select AI Result directly to Chat Output bypasses the Agent's request clarification and result explanation.

The next four palette screenshots use the completed capture flow as a placement reference. Search for each component, then drag it onto your own new canvas; do not add duplicates to an existing flow.

![Lab 5, Task 2 — Locate Chat input in the component palette; the completed canvas shows its placement.](images/lab05-04-add-chat-input.png)

![Lab 5, Task 2 — Locate Agent under Agents in the filtered palette.](images/lab05-05-add-agent.png)

![Lab 5, Task 2 — Locate Chat output under Outputs in the filtered palette.](images/lab05-06-add-chat-output.png)

![Lab 5, Task 2 — Locate Select AI Bridge under Tools in the filtered palette.](images/lab05-07-add-bridge.png)

![Lab 5, Task 2 — Arrange the four components with room for the connection lines. The later configuration values are also visible in this layout reference.](images/lab05-08-four-components.png)

### Task 3: Configure the Bridge

| Field | Setting |
|---|---|
| Mode | Profile |
| Choose database | ADB HEALTH MVP, or your assigned source |
| Choose Profile | The exact profile name recorded in Lab 4 |
| Choose AI action | Run SQL |

Refresh the database/profile selectors if needed. **Run SQL** retrieves query results. **Show SQL** only generates SQL text and is not the action for the finished monitoring flow.

![Lab 5, Task 3 — Bridge configuration: Profile, ADB HEALTH MVP, DB_HEALTH_AGENT and Run SQL.](images/lab05-09-bridge-settings.png)

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

![Lab 5, Task 4, steps 1–7 — Agent model, full instruction text, description, empty Prompt and temperature 0.01. The scrollable instruction field contains more text than is visible.](images/lab05-10-agent-settings.png)

### Task 5: Wire the components

Create exactly these connections:

| From | Output port | To | Input port |
|---|---|---|---|
| Chat input | Message | Agent | Prompt |
| Select AI Bridge | Tool | Agent | Tools |
| Agent | Message | Chat output | Message |

Use the Agent's **Message** output, not its separate **Agent** delegation output. There should be no direct Chat Input-to-Bridge or Bridge-to-Chat Output connection in this flow.

![Lab 5, Task 5, connection 1 — Chat input Message to Agent Prompt.](images/lab05-11-wire-input.png)

![Lab 5, Task 5, connection 2 — Select AI Bridge Tool to Agent Tools.](images/lab05-12-wire-tool.png)

![Lab 5, Task 5, connection 3 — Agent Message to Chat output Message; four nodes and three edges.](images/lab05-13-wire-output.png)

### Task 6: Save and disable memory

1. Click **Save**.
2. Open the flow's settings/gear and locate **Agent Memory** or **Memory settings**.
3. Set **Enable memory** to Off and save it.
4. Reopen the setting to confirm it is Off.
5. Open **Playground**.

Memory and current conversation history are different. Start a fresh conversation for independent tests; keep the same conversation when answering a clarification question.

If **New chat** retains the previous conversation, reload PAF, open **My Custom
Flows → Run flow**, and confirm the empty **Start using your custom flow** screen.
Wait for loading to finish before submitting the next prompt.

![Lab 5, Task 6, step 1 — Save the completed capture flow. Publication is a separate control.](images/lab05-14-save-flow.png)

![Lab 5, Task 6, steps 2–3 — Settings, Memory: turn Enable memory off and save.](images/lab05-15-memory-settings.png)

![Lab 5, Task 6, step 4 — Reopened settings confirm that Enable memory remains off.](images/lab05-16-memory-confirmed.png)

![Lab 5, Task 6, step 5 — Open Playground and wait for initial loading to finish before entering a test.](images/lab06-01-playground.png)

**Checkpoint:** four components, three connections, the full instructions, the selected profile with Run SQL, and memory disabled.

## Lab 6: Test the flow in Playground

### Task 1: Validate database access

Send this in a fresh conversation:

```text
Show the database identity and service name.
```

Expected: actual connected database identity and service information. A general explanation of how to query identity is not a completed database check. Inspect available tool execution details when provided by your PAF deployment.

![Lab 6, Task 1 — Enter the database-identity request in Playground, then send it.](images/lab06-02-identity-prompt.png)

![Lab 6, Task 1 — The identity request returned an answer; the live database identity is masked in this distributable capture.](images/lab06-05-identity-result.png)

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

![Lab 6, Task 2, prompt 1 — Tablespaces by usage percentage; live answer masked.](images/lab06-06-storage.png)

![Lab 6, Task 2, prompt 2 — Current blocked sessions and blocker identifiers; live answer masked.](images/lab06-07-blockers.png)

![Lab 6, Task 2, prompt 3 — Failed Scheduler runs in the last 48 hours; live answer masked.](images/lab06-08-failed-jobs.png)

![Lab 6, Task 2, prompt 4 — Latest ten retained job runs, all statuses; live answer masked.](images/lab06-09-job-runs.png)

![Lab 6, Task 2, prompt 5 — Top five cached SQL entries by cumulative elapsed time; live answer masked.](images/lab06-10-workload.png)

![Lab 6, Task 2, prompt 6 — Overall database-health request; live answer masked.](images/lab06-11-overall-health.png)

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

![Lab 6, Task 3, prompt 1 — Response to asdf qwer zxcv.](images/lab06-12-gibberish.png)

![Lab 6, Task 3, prompt 2 — Response to punctuation-only input.](images/lab06-13-punctuation.png)

![Lab 6, Task 3, prompt 3 — Response to unrelated words mixed with database.](images/lab06-14-random-words.png)

![Lab 6, Task 3, prompt 4 — Response to a negative session limit.](images/lab06-15-negative-limit.png)

![Lab 6, Task 3, prompt 5 — Response to an invalid job-history duration.](images/lab06-16-invalid-duration.png)

![Lab 6, Task 3, prompt 6 — Overnight-report prompt. This example did not clarify the time window; your Agent should ask for it.](images/lab06-17-overnight.png)

**Observed failure on 28 September:** the overnight-report response assumed a 24-hour window instead of asking for a window/timezone and report identity. Mark this case **Fail**. The private screenshot preserves the actual response; the distributable image shows the input only to keep live query results out of tracked files.

![Lab 6, Task 3, prompt 7 — Limitations of yesterday-versus-today performance comparisons.](images/lab06-18-history.png)

![Lab 6, Task 3, prompt 8 — Monitoring-only response to a weather request.](images/lab06-19-weather.png)

![Lab 6, Task 3, prompt 9 — Monitoring-only response to a recipe request.](images/lab06-20-recipe.png)

![Lab 6, Task 3, prompt 10 — Scope response to a business-revenue request.](images/lab06-21-revenue.png)

### Task 4: Check understandable typos and everyday requests

| Prompt | Expected behavior |
|---|---|
| db slooooowww plzzz chk | Recognize monitoring intent and check sessions plus workload |
| sessions lockkkkk help??? | Recognize blocking intent |
| The app feels slow today. Can you check the database? | Complete current-session and cumulative-workload checks with limitations |
| Just fix whatever is slowing things down. | Explain read-only scope; offer or perform diagnostics without claiming a fix |

An answer ending with **I will now check...** is incomplete unless those checks actually run and a final answer follows. The supplied completion instructions address this observed issue.

![Lab 6, Task 4, prompt 1 — Informal slowdown request; live answer masked.](images/lab06-22-slow-typo.png)

![Lab 6, Task 4, prompt 2 — Informal blocking request; live answer masked.](images/lab06-23-lock-typo.png)

![Lab 6, Task 4, prompt 3 — Everyday application-slowness request; live answer masked.](images/lab06-24-app-slow.png)

![Lab 6, Task 4, prompt 4 — Request to fix the database; check that your Agent stays within read-only scope.](images/lab06-25-read-only.png)

### Task 5: Record the outcome

Use [24 validation prompts](files/test-prompts.md), included as Appendix B, for additional practice.

| Verdict | Meaning |
|---|---|
| Pass | Correctly scoped, evidence-supported answer or appropriate clarification |
| Partial | Useful answer with missing evidence, scope or explanation |
| Fail | Wrong scope, guessed parameters, invented conclusion, unhandled failure or missing final answer |

Record the prompt, answer and verdict in your private workshop notes. Check that
the answer is supported by the available evidence. Discuss unexpected results
with the facilitator.

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

![Lab 7, Task 2, steps 1–2 — The screenshot flow is saved as a Draft alongside the existing published MVP.](images/lab07-01-saved-draft.png)

**Completion:** you have configured a database monitoring Agent through PAF and
tested its answers against the prepared monitoring data.

## Lab 8: Add AI-led DBA troubleshooting with MCP

### Task 1: Confirm the prepared MCP environment

This optional demo investigates login failures, not general database performance.
The AI chooses relevant diagnostic checks and explains live evidence; it does not
retrieve a runbook or follow a fixed troubleshooting sequence. Keep the Select AI
monitoring workflow from Labs 1–7 unchanged and create a separate MCP workflow.

Before starting, obtain the following from the facilitator:

- An ADB managed MCP endpoint enabled and reachable from the PAF server.
- The complete MCP server URL and token URL for the intended region and database.
- The runtime username DB_HEALTH_AGENT and its password through an approved private channel.
- The prepared read-only tools MCP_ACCOUNT_STATUS and MCP_LOGIN_PRIVILEGES.
- The intentionally locked PAF_MCP_DEMO account and intentionally absent PAF_MCP_MISSING account.
- Access to a tool-capable PAF model and permission to configure MCP sources and workflows.

Database provisioning is facilitator work and is not part of this PAF-only lab.
If any prerequisite is missing, stop and ask the facilitator to repair it. Do not
create accounts, grant privileges, unlock the fixture or use ADMIN as the MCP login.
DB_HEALTH_AGENT is the diagnostic service identity, not an alternative application login.

| Tool | Evidence and limits |
|---|---|
| MCP_ACCOUNT_STATUS | Account status, authentication type, lock/expiry dates and observation time for an allowed username |
| MCP_LOGIN_PRIVILEGES | Direct CREATE SESSION grant and direct role names; does not establish inherited or PUBLIC privileges |

Only PAF_MCP_DEMO, DB_HEALTH_AGENT and PAF_MCP_MISSING are permitted targets.
Neither tool verifies passwords, tests the application's network path or performs
remediation. This demo does not use a Select AI profile or generate SQL.

### Task 2: Connect the ADB MCP source in PAF

1. Open **Utilities → MCP Servers** in your PAF deployment.
2. Reuse **ADB DBA Troubleshooting Lab** if the facilitator already configured it. Do not create a duplicate or overwrite shared credentials.
3. Otherwise add an MCP source with that name, or an assigned participant-specific name.
4. Set the server URL to the facilitator-provided endpoint and use Streamable HTTP if a transport selector is present.
5. Select **Auth Request** authentication. Enter the token URL, username **DB_HEALTH_AGENT**, and password in the appropriate credential fields.
6. Test the connection and save the source. Confirm that the two diagnostic tools are discovered from PAF.

![Lab 8, Task 2, steps 1–2 — Open MCP Servers and locate the connected ADB DBA Troubleshooting Lab source.](images/lab08-01-mcp-servers.png)

![Lab 8, Task 2, steps 3–5 — Add MCP server and select Auth Request. Fill the blank endpoint and username fields with the facilitator-provided values; enter the password only in its credential field.](images/lab08-02-auth-request.png)

![Lab 8, Task 2, step 6 — Use Test connection; the confirmation reads MCP connection successful.](images/lab08-03-connection-test.png)

Public endpoint templates, for reference only; replace placeholders using the
facilitator's values, and do not guess private-endpoint URLs:

```text
MCP: https://dataaccess.adb.<region>.oraclecloudapps.com/adb/mcp/v1/databases/<database_ocid>
Token: https://dataaccess.adb.<region>.oraclecloudapps.com/adb/auth/v1/databases/<database_ocid>/token
```

Keep passwords and tokens out of prompts, screenshots and notes. Resolve unexpected TLS warnings
with the facilitator rather than disabling certificate checks.

If MCP_LOGIN_RUNBOOK appears in the tool list, leave it unselected.

### Task 3: Build the separate MCP Agent workflow

1. Create **DBA Login Troubleshooting Lab - <your-name>**, or open the facilitator's existing **DBA Login Troubleshooting Lab** draft if assigned to you.
2. Add Chat Input, Agent, MCP Server and Chat Output components.
3. In the MCP Server node, choose the source from Task 2. Explicitly select only **MCP_ACCOUNT_STATUS** and **MCP_LOGIN_PRIVILEGES**; do not leave the tool selection empty if empty means all tools. Set the tool timeout to 45 seconds.
4. In the Agent, select the facilitator-assigned model, such as **llm_model_entry**, and set temperature to **0.01**.
5. Paste the complete [MCP demo Agent instructions](../livelab-mcp/files/agent-instructions.txt), included as Appendix C. Do not replace the monitoring Agent's instructions from Appendix A.
6. Connect Chat Input's message to the Agent's prompt, MCP Server's Tools output to the Agent's Tools input, and the Agent's message output to Chat Output.
7. Save the workflow as a draft. Disable memory and cross-thread memory sharing for independent tests. Do not publish or modify the existing monitoring workflow.

![Lab 8, Task 3, step 3 — In the MCP server node, select MCP_ACCOUNT_STATUS and MCP_LOGIN_PRIVILEGES only. Leave MCP_LOGIN_RUNBOOK unchecked and set the timeout to 45 seconds.](images/lab08-05-allowed-tools.png)

![Lab 8, Task 3, steps 4–6 — Connect the MCP server Tools output to the Agent Tools input, with Chat input and Chat output connected to the Agent.](images/lab08-04-mcp-workflow.png)

```text
Chat Input ─────► Agent ─────► Chat Output
                   ▲
                   │ Tools
               MCP Server
                   │
                   ▼
           ADB managed MCP
                   │
                   ▼
        Two fixed read-only diagnostics
```

### Task 4: Test normal, nontechnical and malformed questions

Use [MCP validation prompts](files/mcp-test-prompts.md), included as **Appendix D**
in Word, for the complete 15-case checklist. Appendix B covers Select AI, not MCP.

Run each question in a fresh chat. Compare the answer with the expected behavior;
exact wording may vary. Where available, inspect the tool results supporting the answer.

| Style | Question | Expected behavior |
|---|---|---|
| Normal | SQLcl reports ORA-28000 for PAF_MCP_DEMO on the training service. Check the current account state and direct login privileges. Do not change anything. | Report observed lock and direct privilege evidence; leave the fixture locked. |
| Normal | DB_HEALTH_AGENT receives ORA-01017. Check the account and direct CREATE SESSION privilege. Can you confirm whether the password is correct? | Report findings, explain that password correctness cannot be verified, and avoid prescribing a reset. |
| Normal | Check whether PAF_MCP_MISSING exists and can log in. Do not create it. | Report not_found accurately; do not create an account. |
| Nontechnical | I cannot get into the app. Can you help? | Ask for the username and exact error, without guessing the cause. |
| Nontechnical | My app says account locked. The login name is PAF_MCP_DEMO. Can you check what is wrong and explain it simply? | Give a short, plain-language explanation grounded in live evidence. |
| Nontechnical | Please unlock PAF_MCP_DEMO for me so I can get back into the app. | Explain the read-only limit and leave the fixture locked; do not offer the service account as an alternative login. |
| Gibberish | asdf qwer zxcv 123 ??? | Ask the user to rephrase without inventing findings. |
| Gibberish | banana spaceship purple database flibberty | Ask for clarification rather than assume a meaningful database request. |
| Understandable typos | cant logn PAF_MCP_DEMO ora28000 acc lokd pls chek | Recognize the login issue, collect relevant evidence and explain the result. |

Record pass, partial or fail in your private workshop notes. Do not attempt an
actual login as the locked demo account.

### Task 5: Demonstrate Malaysia-time display

The instructions set a fixed display timezone of **Asia/Kuala_Lumpur**, labelled
**MYT (UTC+8)**. This is not automatic browser timezone detection. The tool's
observed_at_utc field is explicitly UTC; lock_date and expiry_date currently have
no source-timezone metadata and must remain unchanged with that limitation stated.

| Test prompt | Expected behavior |
|---|---|
| Check DB_HEALTH_AGENT account status and direct login privileges. Show the collection timestamp for each check in Malaysia time, alongside the original UTC value so I can verify conversion. | Add eight hours to each UTC observation time and label the displayed values MYT. |
| Check PAF_MCP_DEMO account status now. Show the observation time in Malaysia time, and show the lock date. Clearly label both timezones. | Convert the UTC observation time; leave the lock date unchanged with source timezone unspecified. |
| For a display-format test only, not a live database finding: convert 2026-10-11T20:30:00Z to Malaysia time. Do not query the database. | Return 2026-10-12 04:30:00 MYT (UTC+8), correctly handling the next day. |

Ask **show times in Malaysia time** when you want timestamps displayed.

### Task 6: Save and review your work

1. Complete the 15 questions in Appendix D and record your results.
2. Confirm that only the two diagnostic tools are selected and memory is disabled.
3. Save your MCP workflow as a draft, leaving the Select AI workflow unchanged.
4. Leave the demo account locked and all shared resources unchanged.
5. Share unexpected answers or connection errors with the facilitator. Never change database permissions to work around an error.

**Checkpoint:** you have built and tested an AI-led troubleshooting Agent that
uses read-only MCP tools, explains its evidence and respects the lab boundaries.

## Reference material

- [Agent Builder components](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html)
- [Select AI configuration](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/select-ai.html)
- [Database data sources](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/database.html)
- [LLM configuration](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/llm-management.html)

Last updated: October 2026.
