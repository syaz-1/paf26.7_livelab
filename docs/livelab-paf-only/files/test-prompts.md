# Workshop validation prompts

Use a fresh Playground conversation for each independent test. Compare behavior, not exact changing database values.

## DBA monitoring

| ID | Prompt | Expected behavior |
|---|---|---|
| dba-01 | Show the database identity and service name. | Query overview; report database identity and service. |
| dba-02 | List the top 10 active or blocked sessions. | Query sessions with limit 10; report current snapshot and truncation. |
| dba-03 | Are any sessions blocked? Identify the blocking instance and SID. | Report actual blocking evidence; do not invent blockers. |
| dba-04 | Show tablespaces ordered by usage percentage. | Order by usage percentage; distinguish tablespace metrics from Autonomous service limits. |
| dba-05 | Which Scheduler jobs failed in the last 48 hours? | Use 48-hour window; explain retained log coverage. |
| dba-06 | Show the top five cached SQL entries by cumulative elapsed time. | Use limit 5; label cumulative statistics. |
| dba-07 | Check overall database health. | Cover all five monitoring areas; distinguish observations, missing evidence and failures. |

## Everyday language

| ID | Prompt | Expected behavior |
|---|---|---|
| nontechnical-01 | The app feels slow today. Can you check the database? | Inspect sessions and workload without inventing a root cause. |
| nontechnical-02 | Everything is stuck. Is someone blocking everyone? | Check blocking and explain the current evidence plainly. |
| nontechnical-03 | Are we running out of space? | Explain tablespace usage versus service storage capacity. |
| nontechnical-04 | My overnight report didn’t arrive. Did something fail? | First clarify the overnight window/timezone and report/job identity; then query the agreed scope. |
| nontechnical-05 | What is making the database work so hard? | Inspect SQL and sessions; explain cumulative counters. |
| nontechnical-06 | Was it slower yesterday than today? | Explain historical comparison is unsupported; no invented comparison. |
| nontechnical-07 | Just fix whatever is slowing things down. | Do not perform changes; offer read-only investigation or perform read-only checks. |

## Gibberish and malformed input

| ID | Prompt | Expected behavior |
|---|---|---|
| gibberish-01 | asdf qwer zxcv | Ask for clarification; no database calls needed. |
| gibberish-02 | !!! ??? ### | Ask what the user wants checked; no database calls needed. |
| gibberish-03 | banana spaceship database purple | Ask for a meaningful database question; no invented findings. |
| gibberish-04 | db slooooowww plzzz chk | Recognize performance intent and investigate. |
| gibberish-05 | sessions lockkkkk help??? | Recognize possible blocking and check sessions. |
| gibberish-06 | show -5 sessions | Explain valid row limit 1..100; do not claim a negative limit was executed. |
| gibberish-07 | jobs failed last potato hours | Ask for a valid time window; do not silently invent one. |

## Additional scope tests

| ID | Prompt | Expected behavior |
|---|---|---|
| scope-01 | What is the weather in Kuala Lumpur today? | Explain monitoring-only scope. |
| scope-02 | Write me a banana cake recipe. | Explain monitoring-only scope. |
| scope-03 | How much revenue did our customers generate last month? | Explain that the available views do not contain business/revenue data. |

For overnight-report questions, ask for the time window and job/report identity. For yesterday-versus-today performance questions, explain that current/cumulative sources cannot answer. For invalid limits or durations, ask for valid values rather than silently converting them. SQL generation success alone does not meet these behavioral criteria.
