# Existing system-view access for Select AI

On 2026-09-24 the user approved direct SELECT access for DB_HEALTH_AGENT to five existing SYS monitoring views. Applied with the prescribed SQLcl and ADMIN saved connection after asserting the database and session identity:

- SYS.GV_$SESSION
- SYS.GV_$SQLSTATS
- SYS.DBA_TABLESPACE_USAGE_METRICS
- SYS.DBA_TABLESPACES
- SYS.DBA_SCHEDULER_JOB_RUN_DETAILS

Script: db/07_select_ai_monitoring_grants.sql. All five grants succeeded without grant option. Bounded reads as DB_HEALTH_AGENT succeeded for all five; no live rows were printed or stored here. Direct SELECT exposes all columns in these views, unlike the narrower output of the existing health package. No catalog role was granted and DB_HEALTH_API was not modified.

Agent Factory discovery checks found an additional limitation:

- Select AI schema-owner endpoint omits SYS.
- Explicit SYS object metadata request succeeds and lists the three DBA_* views above.
- That same object list does not include GV_$SESSION or GV_$SQLSTATS.

Therefore database permissions are ready, but selecting all five through the current UI is not verified and is blocked by discovery behavior. Do not grant more privileges to compensate without evidence. A subsequent step can test an explicitly configured profile object_list and metadata support for the two dynamic performance views. No profile was created or modified in this step; provider/profile configuration is still required.

## UI workaround implemented

At the user's request, ADMIN provisioned five same-schema wrapper views using `db/08_select_ai_monitoring_views.sql`. No permanent CREATE VIEW privilege was granted to the runtime account. All five are VALID, have READ_ONLY=Y, pass bounded runtime reads, and appear in Agent Factory's Select AI object-list endpoint under DB_HEALTH_AGENT:

- MONITOR_DATABASE_OVERVIEW
- MONITOR_SESSIONS
- MONITOR_STORAGE_USAGE
- MONITOR_FAILED_JOBS
- MONITOR_SQL_WORKLOAD

These are live views, not persisted snapshots. Sessions include active or blocked user sessions. Failed jobs cover retained failed runs without a built-in time window; generated SQL must apply the requested window. SQL statistics are cumulative. Comments describe these scopes. SQL text, bind values and job output are not projected. The previously authorized direct SYS grants remain in place, so these projections alone do not restrict all access available to the account.

In the UI, refresh or reopen profile creation, select DB_HEALTH_AGENT, select only these five views, use object-list mode All and enable Enforce Object List where available. Profile validation and model-driven query execution remain to be tested after provider/profile setup. The original health package and agent flow were not changed.

## MVP simplification: all job-run statuses

Created MONITOR_JOB_RUNS via db/09_monitor_job_runs.sql at the user's request. It exposes retained Scheduler runs without a status/time filter, plus requested/actual start dates, duration in seconds and instance ID. Runtime reads, duration expression, VALID/READ_ONLY metadata and Agent Factory picker discovery all passed. No new grants were needed.

Select MONITOR_JOB_RUNS instead of MONITOR_FAILED_JOBS in the NL2SQL object list. Existing profiles were not changed, and the failed-only view remains for compatibility. The new view is run history, not a list of job definitions or currently running jobs.
