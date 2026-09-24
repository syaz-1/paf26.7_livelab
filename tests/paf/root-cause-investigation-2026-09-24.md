# PAF tool availability investigation — 2026-09-24

No database, flow, prompt, model or memory changes were applied during this investigation. The local HTTP helper gained raw-response support to download diagnostic evidence.

## Evidence

Compared memory-disabled test records against the application diagnostic ZIP collected at 01:12:37 UTC. Raw diagnostics remain in ignored `.local/paf-investigation/diagnostics.zip`; live answers remain in ignored `.local/paf-tests/20260924T005315Z/`. References below are line numbers in the ZIP's `application_logs/agent_factory_logs/agent_factory.log`.

| Case | Application log lines | Observed behavior |
|---|---|---|
| dba-02: top active/blocked sessions | 5900–5959 | “Unavailable” answer; no executor discovery or execution event in the request interval. |
| dba-03: blocked sessions | 5965–6027 | Discovery finds five routines; GET_SESSIONS executes at line 6023 and the answer contains current data. |
| dba-07: overall health | 6298–6329 | “Unavailable” answer; no executor discovery or execution event. |
| nontechnical-04: failed overnight report | 6527–6558 | “Unavailable” answer; no executor discovery or execution event. |
| dba-05: failed jobs over 48 hours | 6131–6224 | GET_DATABASE_OVERVIEW and GET_FAILED_JOBS execute; the latter logs only `binds=['return_value']` at line 6220. |
| gibberish-04: misspelled slow-database request | 6787–6946 | Four routines execute, followed by a response reporting no user-facing output. Separate response-generation problem. |

The failed answers themselves distinguish generic PL/SQL discovery/execution tools from the GET_* names in the live instructions. The instructions call those routine names “tools” without describing the discovery/execution sequence.

## Findings and confidence

1. **Confirmed failure location:** sampled “unavailable” answers occur without a logged executor attempt. The same connection/schema/package works in the adjacent blocked-session test. There is no evidence that missing database grants or the earlier cross-schema discovery limitation causes these sampled failures.
2. **Leading root-cause hypothesis:** the model treats GET_* routine names in its instructions as standalone callable tool names, and sometimes stops instead of using the generic PL/SQL discovery/execution tools. Final answers and execution logs strongly support this, but the exact model-facing tool schema and raw model tool calls were not captured, so prompt mismatch versus a runtime tool-registration issue cannot be conclusively separated.
3. **Separate argument-handling defect:** the 48-hour job request reaches GET_FAILED_JOBS with no logged input binds. The package default is 24 hours. Together with the independent 48-hour database check and the incorrect answer, this strongly indicates the requested window was lost. Logs do not establish whether the model omitted the argument or the executor dropped/misinterpreted it.
4. **Memory is not the sole cause:** failures persist with memory disabled. Earlier memory persistence exceptions (`NoneType.content`) occurred on September 23 at 17:04 UTC, before this retest; they do not establish a cause for these requests.
5. **No-output failures need separate diagnosis:** the misspelled request did invoke four approved routines, so its placeholder answer cannot be explained by unavailable tools alone.

## Limits and next controlled investigation

No tracing provider is configured; logs explicitly say tracing is disabled. Normal diagnostics record discovery and routine invocation but not the complete model request, tool schema, arguments and returned tool messages. Request intervals were matched by room ID; executor entries themselves lack room IDs, so time-window attribution is strongest for these sequential tests and is not a substitute for spans.

Before selecting a definitive fix, capture one failing and one successful fresh-chat turn with model/tool tracing, protecting credentials and live results. Compare the actual registered tool names, discovery response, execution arguments and final model response. For the jobs defect, specifically inspect whether `P_HOURS_BACK=48` reaches the executor. A controlled discovery-first prompt experiment could then test the leading hypothesis without modifying the published agent.

Do not add grants or move monitoring queries into the login schema based on these failures. Existing evidence supports investigating agent orchestration and argument handling first.
