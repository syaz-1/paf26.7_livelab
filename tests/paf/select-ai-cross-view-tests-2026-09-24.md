# Select AI cross-view tests — 2026-09-24

Executed five fresh-chat requests against the user-supplied integration endpoint for the Select AI monitoring workflow. No profile attributes, enforcement settings, grants or view definitions changed. The API key is not saved in this report or result artifacts.

| Test | Outcome |
|---|---|
| Database name and service from MONITOR_DATABASE_OVERVIEW | PASS: returned a result table |
| Row count from MONITOR_SESSIONS | PASS: returned a result table |
| Tablespace name and usage from MONITOR_STORAGE_USAGE | FAIL: ORA-20004 object-list rejection |
| Top three SQL IDs by cumulative elapsed seconds from MONITOR_SQL_WORKLOAD | PASS: returned three rows |
| Job-run counts grouped by status from MONITOR_JOB_RUNS, without date filter | FAIL: ORA-20004 object-list rejection |

All HTTP responses were 200; the failure classification is based on the message content. All five room IDs were distinct.

The storage failure includes generated SQL referencing only DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE, which is an approved profile object. Therefore that particular failure is not explained by the generated SQL naming an unlisted view. Job aggregation also fails without a date predicate, narrowing the problem beyond the original 48-hour condition.

Current evidence points to enforcement behavior for particular dictionary-backed views; it does not establish the exact internal validation rule or prove that every dictionary-backed view fails. Ordinary wrapper views are not universally broken: overview, sessions and SQL workload worked. Direct SQL reads of all wrappers succeeded in earlier tests.

Raw responses and room IDs remain private in `.local/select-ai-error/cross-view-tests.json`. The failing storage request has correlation reference 9e05c3b5-f0c9-4573-8baf-c354f7991aab; the failing job request has reference 169c65dc-e9d4-449f-aed3-c3721a2752d1.
