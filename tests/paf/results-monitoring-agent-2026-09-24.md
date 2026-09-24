# New monitoring Agent flow — 24 September 2026

Flow: ADB Health Monitoring Agent MVP (`5C2A338670CA1162E0634815000AC353`). Chat Input -> Agent -> Chat Output, with native Select AI Bridge connected as the Agent tool. Existing OCI model, DB_HEALTH_AGENT profile, Run SQL action; memory disabled. Database grants, view definitions and profile enforcement settings were not changed.

Created as a draft. Later verification found publication enabled with unchanged component values; the assistant did not issue a publish operation. Subsequent targeted instruction correction preserved the observed publication state and graph layout.

## Initial regression

Ran all 21 original prompts plus three out-of-scope questions using the authenticated owner run API. All 24 returned HTTP 200 in distinct rooms. Responses were reviewed semantically; HTTP success alone was not counted as a behavioral pass.

All ten clarification/scope cases returned the expected behavior:

| Cases | Behavior observed |
|---|---|
| gibberish-01, 02, 03 | Asked to rephrase; no arbitrary database results returned. |
| gibberish-06 | Asked for a valid positive integer limit rather than changing -5 into 5. |
| gibberish-07 | Asked for a valid duration rather than guessing 24 hours. |
| nontechnical-04 | Asked for overnight time window and job/report identity. |
| nontechnical-06 | Explained that current/cumulative views cannot compare yesterday with today. |
| scope-01, 02, 03 | Declined weather, recipe and customer-revenue questions as outside monitoring scope. |

Supported checks returned database identity, current sessions/blockers, sorted tablespace usage, recent job results and cumulative SQL rankings. Storage output correctly distinguished tablespace capacity from Autonomous service storage limits. Recognizable slowdown and locking typos were handled as monitoring requests. A request to fix performance received an explanation of read-only scope.

Remaining issues in the initial run:
- Overall health (dba-07) returned the PAF placeholder 'The flow finished without a user-facing response.' Application logs show several Select AI Bridge invocations followed by an empty display-only response; the exact runtime/model cause is not established.
- General slowdown (nontechnical-01) returned session findings but ended with a promise to perform additional checks.
- Workload (nontechnical-05) returned cumulative SQL findings but ended with another promised check; session coverage was absent from the final answer.
- Recent failed-job output omitted the retained-log caveat.
- Some answers omitted an actual observation timestamp or described session wait events imprecisely. No blanket all-tests-pass claim is made.

## Targeted correction

Added completion rules to the Agent instructions: finish required tool calls before answering, never end with 'I will now check', use two focused calls for general slowdown/workload (sessions and cumulative SQL), provide a final summary or explicitly state missing checks, and retain the log-coverage caveat even for no matching failures.

Retesting is limited to affected checks and a gibberish control; the original full run remains the baseline, rather than being relabeled as a complete regression of the revised prompt.

## Evidence and limitations

Private original responses: `.local/paf-tests/monitoring-agent-20260924T095803Z/`.
Private targeted responses: `.local/new-monitoring-flow/completion-retest.json`.
Saved instructions: `docs/monitoring-agent-instructions.txt`.
Test runner: `scripts/test_monitoring_agent.py`.

API final answers do not include complete tool traces or generated SQL. Clarification tests establish user-facing behavior, not a deterministic guarantee of no monitoring query. The Bridge also retrieves profile metadata during graph initialization, so rejecting a question does not imply zero database connections. No tracing provider was enabled or changed. The Agent instructions are not a substitute for database permissions or deterministic parameter validation; profile object-list enforcement remains disabled.


## Completion-rule retest

Five targeted requests completed with HTTP 200 after the first instruction correction:

- Failed jobs now explicitly states that the last-48-hours result covers retained logs.
- General slowdown returned both a session finding and cumulative SQL findings, without a promise to continue.
- Workload returned session and cumulative SQL findings in one answer. Its explanation still risks overinterpreting cumulative resource use as a cause; SQL semantics and causal claims require review.
- Gibberish still asks for clarification.
- Overall health again returned no user-facing response. The prompt-only instruction to complete five areas did not fix this case.

The next targeted adjustment reduces overall health to two calls: a one-row summary using identity plus independent session/storage/job aggregates, then top cumulative SQL. This is a bounded workflow workaround, not a proven diagnosis of a runtime iteration limit.


## Final overall-health retest and saved state

The two-call overall-health strategy returned a complete answer with database identity and observation time, active/blocked session counts, maximum tablespace usage, last-24-hours failed-job count, top-five cumulative SQL and relevant scope limitations. The no-user-facing-response placeholder did not recur in this targeted test. This is one successful reproduction, not a guarantee across all future model outputs.

Final verification: four native components, three intended connections, custom instructions match the saved local file, memory disabled, publication state enabled and preserved. Private final overall-health response: `.local/new-monitoring-flow/overall-compact-retest.json`.

The ten clarification/scope cases passed in the full baseline run; a gibberish control passed after the completion change. The final overall-health-only change was tested on overall health. No full 24-case rerun was performed after that final targeted change. Individual database observations are live and were not asserted equal across different query times.
