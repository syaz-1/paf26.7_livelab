-- Workshop provisioning only. Run once as ADMIN using SQLcl.
-- Usage: @docs/livelab/files/prepare-monitoring.sql YOUR_EXPECTED_DB_NAME
-- Argument is a trusted DB_NAME identifier, not a connect string or password.
-- DB_HEALTH_AGENT must already exist. Existing MONITOR_* views are not replaced.
set echo off
set verify off
set history off
set define on
whenever sqlerror exit failure rollback
whenever oserror exit failure rollback

declare
  n number;
begin
  if sys_context('USERENV','SESSION_USER') <> 'ADMIN'
     or sys_context('USERENV','DB_NAME') <> '&1' then
    raise_application_error(-20030,'Unexpected database or login; stopping.');
  end if;
  select count(*) into n from dba_users where username='DB_HEALTH_AGENT';
  if n <> 1 then
    raise_application_error(-20031,'Provision DB_HEALTH_AGENT before this script.');
  end if;
  select count(*) into n from dba_objects
  where owner='DB_HEALTH_AGENT' and object_name in
    ('MONITOR_DATABASE_OVERVIEW','MONITOR_SESSIONS','MONITOR_STORAGE_USAGE',
     'MONITOR_SQL_WORKLOAD','MONITOR_JOB_RUNS');
  if n <> 0 then
    raise_application_error(-20032,'Monitoring objects already exist. Inspect and use verification; do not overwrite.');
  end if;
end;
/
set define off

grant execute on DBMS_CLOUD to DB_HEALTH_AGENT;
grant execute on DBMS_CLOUD_AI to DB_HEALTH_AGENT;
grant select on SYS.GV_$SESSION to DB_HEALTH_AGENT;
grant select on SYS.GV_$SQLSTATS to DB_HEALTH_AGENT;
grant select on SYS.DBA_TABLESPACE_USAGE_METRICS to DB_HEALTH_AGENT;
grant select on SYS.DBA_TABLESPACES to DB_HEALTH_AGENT;
grant select on SYS.DBA_SCHEDULER_JOB_RUN_DETAILS to DB_HEALTH_AGENT;

create view DB_HEALTH_AGENT.MONITOR_DATABASE_OVERVIEW as
select sys_context('USERENV','DB_NAME') database_name,
       sys_context('USERENV','CON_NAME') container_name,
       sys_context('USERENV','SESSION_USER') session_user_name,
       sys_context('USERENV','SERVICE_NAME') service_name,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.dual with read only;
comment on table DB_HEALTH_AGENT.MONITOR_DATABASE_OVERVIEW is
'Database identity and current connection reachability only; not an overall health assessment.';

create view DB_HEALTH_AGENT.MONITOR_SESSIONS as
select inst_id instance_id, sid, serial# serial_number, username, status,
       sql_id, event, wait_class, state wait_state, seconds_in_wait,
       blocking_session_status,
       case when blocking_session_status = 'VALID' then blocking_instance end blocking_instance_id,
       case when blocking_session_status = 'VALID' then blocking_session end blocking_sid,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.gv_$session
where type = 'USER' and (status = 'ACTIVE' or blocking_session_status = 'VALID')
with read only;
comment on table DB_HEALTH_AGENT.MONITOR_SESSIONS is
'Current active or blocked user sessions visible in this container across instances. Not historical data. VALID blocking_session_status identifies a known blocker.';
comment on column DB_HEALTH_AGENT.MONITOR_SESSIONS.seconds_in_wait is
'Interpret with WAIT_STATE; this is not always the duration of a current wait.';

create view DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE as
select m.tablespace_name, m.used_percent,
       m.used_space * t.block_size used_bytes,
       m.tablespace_size * t.block_size capacity_bytes,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.dba_tablespace_usage_metrics m
join sys.dba_tablespaces t on t.tablespace_name = m.tablespace_name
with read only;
comment on table DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE is
'Tablespace capacity including autoextend considerations. Not Autonomous service provisioned storage or OCI StorageUtilization.';

create view DB_HEALTH_AGENT.MONITOR_SQL_WORKLOAD as
select inst_id instance_id, sql_id, plan_hash_value, executions,
       elapsed_time / 1000000 elapsed_seconds,
       cpu_time / 1000000 cpu_seconds,
       elapsed_time / nullif(executions,0) / 1000000 average_elapsed_seconds,
       buffer_gets, disk_reads, rows_processed,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.gv_$sqlstats
where executions > 0
with read only;
comment on table DB_HEALTH_AGENT.MONITOR_SQL_WORKLOAD is
'Cumulative cached statistics per instance and SQL entry, not a last-N-hours report. Order by ELAPSED_SECONDS descending for top SQL. SQL text and bind values omitted. Does not alone establish current slowness or its cause.';

create view DB_HEALTH_AGENT.MONITOR_JOB_RUNS as
select owner job_owner, job_name, log_id, log_date,
       sys_extract_utc(log_date) log_date_utc,
       status, error# error_number,
       req_start_date requested_start_date,
       actual_start_date,
       extract(day from run_duration) * 86400
         + extract(hour from run_duration) * 3600
         + extract(minute from run_duration) * 60
         + extract(second from run_duration) run_duration_seconds,
       instance_id,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.dba_scheduler_job_run_details
with read only;
comment on table DB_HEALTH_AGENT.MONITOR_JOB_RUNS is
'All retained Scheduler run history visible in this container, without a status or time filter. Filter STATUS for failed or successful runs and LOG_DATE for the requested time window. Not job definitions or a live running-job inventory. Jobs with no retained runs are absent.';
comment on column DB_HEALTH_AGENT.MONITOR_JOB_RUNS.run_duration_seconds is
'Run duration in seconds; NULL when unavailable.';

select o.object_name, o.status, v.read_only
from dba_objects o join dba_views v
  on v.owner=o.owner and v.view_name=o.object_name
where o.owner='DB_HEALTH_AGENT' and o.object_type='VIEW'
  and o.object_name in ('MONITOR_DATABASE_OVERVIEW','MONITOR_SESSIONS',
    'MONITOR_STORAGE_USAGE','MONITOR_SQL_WORKLOAD','MONITOR_JOB_RUNS')
order by o.object_name;
