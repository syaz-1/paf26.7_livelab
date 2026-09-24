# Agent Factory retest after instruction change — 2026-09-24

Ran all 21 saved prompts against the published agent in fresh chats. Verified the revised instructions were active and memory was disabled. No deployed settings or database code were modified by the tester.

## Result

- 21/21 requests returned HTTP 200 and a user-facing answer in distinct rooms.
- Zero answers claimed the health routines were unavailable.
- Zero responses contained the previous no-user-facing-response placeholder.
- Each of the five approved routines was executed somewhere in this suite.
- This is improvement in tool access, not a complete behavioral pass: four multi-check cases omitted an expected routine.

## Three priority checks

| Check | Result and evidence |
|---|---|
| Top 10 active/blocked sessions | GET_SESSIONS executed with an input-limit bind; returned session data. |
| Blocked sessions | GET_SESSIONS executed; blocking question answered. |
| Failed jobs over 48 hours | GET_FAILED_JOBS executed with an hours-back input bind; answer included the failure omitted by the previous default-window run. |

Diagnostics show bind names, not values. Consequently the session limit value 10 and hours-back value 48 are not directly verified by these logs. The job answer is consistent with the requested 48-hour window and the previously independently verified failure, rather than the previous 24-hour result. Exact argument-value verification still requires tool traces.

## Remaining gaps

1. Overall health executes only overview; the answer admits that it has not assessed overall health.
2. Normal and typo-heavy slow-app requests check sessions but stop before SQL workload, despite promising to continue.
3. The heavy-workload request checks SQL but omits sessions and opens with a causal claim that cumulative counters alone do not establish.
4. Some answers omit collection timestamps, truncation/coverage notes and the tablespace-versus-service-capacity distinction.
5. The negative-limit reply omits the valid integer range 1–100.
6. The invalid “potato hours” request correctly asks for clarification, but unexpectedly executes GET_SESSIONS first. It does not execute GET_FAILED_JOBS.

## Case review

| Case | Finding |
|---|---|
| dba-01 | Overview executed; identity/service returned; collection timestamp omitted. |
| dba-02 | Sessions executed with input-limit bind; result returned; collection timestamp and truncation context omitted. |
| dba-03 | Sessions executed and blocking question answered. |
| dba-04 | Storage executed; percentages returned; service-capacity distinction omitted. |
| dba-05 | Jobs executed with hours-back input bind; previously missed failure returned in the 48-hour answer; retention caveat omitted. |
| dba-06 | SQL workload executed with limit input bind; five cumulative entries returned; truncation context omitted. |
| dba-07 | Only overview executed; correctly admits this is not an overall assessment, but task remains incomplete. |
| nontechnical-01 | Overview and sessions executed; SQL workload omitted; promises continuation but turn ends. |
| nontechnical-02 | Sessions executed; blocking question answered. |
| nontechnical-03 | Storage executed; service-capacity distinction omitted. |
| nontechnical-04 | Failed jobs executed; explains no failures does not prove report success. |
| nontechnical-05 | SQL workload executed; sessions omitted; opening causal assertion is stronger than cumulative evidence supports. |
| nontechnical-06 | Correctly explains historical comparison is unavailable. |
| nontechnical-07 | Maintains read-only boundary and asks for symptoms. |
| gibberish-01 | Clarification, no routine execution. |
| gibberish-02 | Clarification, no routine execution. |
| gibberish-03 | Clarification, no routine execution. |
| gibberish-04 | Sessions executed; promises SQL workload check but no such execution occurs before completion. |
| gibberish-05 | Sessions executed; explains blocking evidence. |
| gibberish-06 | Rejects negative limit; omits integer range 1–100. |
| gibberish-07 | Asks for valid hours, but logs an unrelated GET_SESSIONS call. |

## Evidence and interpretation

Private raw responses, diagnostic ZIP and room-correlated execution summaries are in `.local/paf-tests/20260924T012033Z/`. Executor log entries are attributed by each room's processing interval; they do not themselves carry room IDs. The suite ran sequentially. No model/tool span provider was enabled.

This run supports the instruction/tool-name mismatch hypothesis: after the user changed the instructions, unavailable refusals disappeared and explicit input binds appeared. One run does not prove long-term reliability or exclude other runtime defects. Database observations are time-dependent.

The next targeted instruction change should require completing all checks for broad health/performance requests before answering, preserving scope/timestamp caveats, and clarifying invalid inputs before making any database call. That change has not been applied.
