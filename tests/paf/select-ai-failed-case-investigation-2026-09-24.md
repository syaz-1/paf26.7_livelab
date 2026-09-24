# Nine failed cases: investigation

## Verified configuration

The published flow consists of Chat Input -> Select AI (runsql) -> Chat Output, using profile DB_HEALTH_AGENT. There is no Agent node or separate clarification/result-interpretation step. Memory is disabled. The stored profile has max_tokens=4096 and enforce_object_list=false. No explicit stored instructions, comments, annotations, constraints, conversation or temperature attributes were returned by the inspection query; absence does not establish their effective defaults.

The view comments describe current/cumulative scope and retained Scheduler history correctly. Their inclusion in the actual model request has not been verified.

## Findings

| Failed case | Evidence | Interpretation and remaining check |
|---|---|---|
| dba-04: usage ordering | Returned alphabetical tablespaces; percentages are not ordered | Sorting requirement was lost or changed. Need generated SQL to distinguish missing ORDER BY from result-processing changes. |
| nontechnical-01: app slow today | Empty result list only | No explanatory or multi-check response. Cannot infer why the query found no rows without generated SQL. |
| nontechnical-04: overnight report | Old failures returned, capped at 50 displayed rows | Response does not answer the recent/report-specific question. All-retained-history view requires a generated date filter; original query is unavailable. |
| nontechnical-06: yesterday versus today | Definitive NO and today-labelled average | Unsupported conclusion using the configured current/cumulative views. COLLECTION timestamp is observation time, not an execution-history timestamp; whether SQL confused them remains a hypothesis. |
| gibberish-01 | Database overview returned for nonsense | No clarification behavior; arbitrary query selection. |
| gibberish-02 | Database overview returned for punctuation | No clarification behavior; arbitrary query selection. |
| gibberish-03 | Empty list returned for nonsense | No clarification behavior; original generated predicate unknown. |
| gibberish-06 | Session data returned for negative limit | Negative input not rejected or explained; actual limit translation unknown. The old 1..100 bound belonged to the fixed API and is not inherently imposed by direct Select AI. |
| gibberish-07 | Empty list for potato hours | Invalid time window not clarified; actual generated filter unknown. |

The direct Run SQL architecture is a verified contributor to poor conversational behavior, not proof of the exact SQL-generation cause of every failure. Error-free execution does not establish semantic correctness.

## Attempted deeper verification

Searched GV_$SQLSTATS for SQL containing MONITOR_ active during the original suite window: zero cached queries returned. This does not prove that no queries ran; cache retention/reuse can prevent recovery. A prior alias-specific lookup recovered only the diagnostic bind-assignment SQL, not the historical test query.

The first attempt to run nine SHOWSQL reproductions required separate approval for sending the prompts and five-view schema metadata directly to OCI Generative AI us-chicago-1, model google.gemini-2.5-flash. The user subsequently approved that payload and destination. The approved investigation is recorded below.


## Approved SHOWSQL investigation — 24 September 2026

Executed nine DBMS_CLOUD_AI.GENERATE calls with action=showsql as DB_HEALTH_AGENT through the prescribed SQLcl, using the existing DB_HEALTH_AGENT profile. Verified database and session identity before the calls. All nine returned SQL without generation errors. **None of the generated statements was executed.** No profile, grants, views or flow settings were changed.

These are fresh translations, not recovered original queries. They demonstrate failure mechanisms in this reproduction but cannot establish the exact SQL used during the original integration run.

| Case | Generated SQL evidence | Finding |
|---|---|---|
| dba-04 | ORDER BY T1."USED_PERCENT" ASC | Usage sorting is present this time. The prompt does not specify ascending/descending, so ASC meets its ordering requirement. Original name-order failure not reproduced; cannot attribute it conclusively to generation or output handling. |
| nontechnical-01 | Only MONITOR_SESSIONS; filters ACTIVE and WAITING, and COLLECTED_AT_UTC = (SELECT MAX(COLLECTED_AT_UTC) ...); top 10 by SECONDS_IN_WAIT | Narrows a general slowdown check to currently waiting active sessions, omits workload evidence and treats a live view like stored snapshots. Empty results under these predicates do not rule out slowness. Timestamp-equality effects were not executed or measured. |
| nontechnical-04 | MONITOR_JOB_RUNS WHERE UPPER(STATUS) = UPPER('FAILED'); no date filter or ORDER BY | Confirms loss of overnight scope in this reproduction. All retained failures can match; returned order is unspecified. No report/job identity is requested. |
| nontechnical-06 | Groups MONITOR_SQL_WORKLOAD by TRUNC(COLLECTED_AT_UTC), averages ELAPSED_SECONDS, compares yesterday > today with ELSE 'NO' | Invalid historical interpretation: COLLECTED_AT_UTC is generated from current SYSTIMESTAMP, not a stored sample date. ELAPSED_SECONDS is a cumulative cached counter. Missing yesterday aggregate yields NULL; comparison is not true and falls into NO, conflating missing evidence with a negative answer. |
| gibberish-01 | Unfiltered SELECT from MONITOR_DATABASE_OVERVIEW | Arbitrary database query for nonsense; no clarification. |
| gibberish-02 | Unfiltered SELECT from MONITOR_DATABASE_OVERVIEW | Arbitrary database query for punctuation; no clarification. |
| gibberish-03 | Database name LIKE '%banana%' AND LIKE '%spaceship%' AND LIKE '%purple%' | Interprets nonsense as literal name-search predicates; empty results replace clarification. |
| gibberish-06 | FETCH FIRST 5 ROWS ONLY | Silently changes negative five to positive five. |
| gibberish-07 | ACTUAL_START_DATE >= SYSTIMESTAMP - INTERVAL '24' HOUR | Invents a 24-hour window for 'potato hours' rather than asking for a valid duration. |

### Why the historical answer is wrong

The generated CASE is effectively:

```sql
CASE WHEN yesterday_average > today_average THEN 'YES' ELSE 'NO' END
```

With no yesterday group, yesterday_average is NULL. That does not establish that yesterday was faster or equally fast. The current/cumulative view cannot supply the requested comparison in the first place. A NULL-aware CASE alone would not make this source suitable for historical performance analysis. Also, AVG(ELAPSED_SECONDS) across cached entries is not an execution-weighted average response time.

### Recommended fixes, in priority order

1. Add an Agent step to clarify nonsense, invalid limits and invalid time windows before invoking a database tool; interpret empty results instead of passing [] straight to chat. For MVP checks needing guaranteed bounds, prefer the existing fixed monitoring API routines with validated parameters. Agent instructions alone are not deterministic validation.
2. Explicitly reject yesterday-versus-today performance comparisons when only these current/cumulative views are available. Explain that stored historical samples would be required. Document COLLECTED_AT_UTC as query observation time in column metadata; verify whether profile comment settings include that metadata before relying on it.
3. For overnight jobs, ask for the report/job and time window or clearly state an agreed default with timezone. Use an explicit bounded time filter on the appropriate job event timestamp and newest-first ordering. Do not silently search all retained failures.
4. For general slowness, inspect both current sessions and cumulative workload, label those scopes and avoid claiming a root cause from an empty wait query. Do not choose a latest snapshot by MAX(COLLECTED_AT_UTC) on a live view.
5. Make storage ordering explicit, e.g. highest USED_PERCENT first, and verify both generated SQL and returned ordering on the next controlled regression. This single reproduction did not reproduce the original ordering failure.

These are proposed fixes, not applied changes. Disabling object-list enforcement removed the earlier execution rejection but does not validate the meaning of generated SQL. Raising max_tokens likewise does not address these semantic failures.

Private generated SQL: .local/paf-tests/select-ai-20260924T042155Z/failed-showsql-reproduction.txt (mode 0600). No credentials or live query rows are included in this report.
