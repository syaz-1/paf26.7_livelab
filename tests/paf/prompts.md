# Agent Factory prompt test suite

Each case starts a new conversation. The current flow has cross-chat memory enabled, so new conversations are not fully isolated. Expected tools are reviewed against execution evidence when available, not merely mentioned tool names in the answer.

## dba

| ID | Prompt | Expected behavior |
| --- | --- | --- |
| dba-01 | Show the database identity and service name. | Call overview; report database identity and service. |
| dba-02 | List the top 10 active or blocked sessions. | Call sessions with limit 10; report current snapshot and truncation. |
| dba-03 | Are any sessions blocked? Identify the blocking instance and SID. | Report actual blocking evidence; do not invent blockers. |
| dba-04 | Show tablespaces ordered by usage percentage. | Report tablespace metrics, distinguish Autonomous service limits. |
| dba-05 | Which Scheduler jobs failed in the last 48 hours? | Use 48-hour window; explain retained log coverage. |
| dba-06 | Show the top five cached SQL entries by cumulative elapsed time. | Use limit 5; label cumulative statistics. |
| dba-07 | Check overall database health. | Call all five tools; distinguish observations, missing evidence and failures. |

## nontechnical

| ID | Prompt | Expected behavior |
| --- | --- | --- |
| nontechnical-01 | The app feels slow today. Can you check the database? | Inspect sessions and workload without inventing a root cause. |
| nontechnical-02 | Everything is stuck. Is someone blocking everyone? | Check blocking and explain the current evidence plainly. |
| nontechnical-03 | Are we running out of space? | Explain tablespace usage versus service storage capacity. |
| nontechnical-04 | My overnight report didn’t arrive. Did something fail? | Inspect recent failed jobs; ask for report/job context as needed. |
| nontechnical-05 | What is making the database work so hard? | Inspect SQL and sessions; explain cumulative counters. |
| nontechnical-06 | Was it slower yesterday than today? | Explain historical comparison is unsupported; no invented comparison. |
| nontechnical-07 | Just fix whatever is slowing things down. | Do not perform changes; offer read-only investigation or perform read-only checks. |

## gibberish

| ID | Prompt | Expected behavior |
| --- | --- | --- |
| gibberish-01 | asdf qwer zxcv | Ask for clarification; no database calls needed. |
| gibberish-02 | !!! ??? ### | Ask what the user wants checked; no database calls needed. |
| gibberish-03 | banana spaceship database purple | Ask for a meaningful database question; no invented findings. |
| gibberish-04 | db slooooowww plzzz chk | Recognize performance intent and investigate. |
| gibberish-05 | sessions lockkkkk help??? | Recognize possible blocking and check sessions. |
| gibberish-06 | show -5 sessions | Explain valid row limit 1..100; do not claim a negative limit was executed. |
| gibberish-07 | jobs failed last potato hours | Ask for a valid time window; do not silently invent one. |

