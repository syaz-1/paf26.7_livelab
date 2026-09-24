-- UI-discoverable read-only monitoring projections, provisioned as ADMIN.
-- Existing direct source grants belong to DB_HEALTH_AGENT.
whenever sqlerror exit failure rollback
begin
  if sys_context('USERENV','SESSION_USER') <> 'ADMIN'
     or sys_context('USERENV','DB_NAME') <> 'G2C3435895384DA_DEMO' then
    raise_application_error(-20030, 'Unexpected database or session user; stopping.');
  end if;
end;
/
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

create view DB_HEALTH_AGENT.MONITOR_FAILED_JOBS as
select owner job_owner, job_name, log_id, log_date,
       sys_extract_utc(log_date) log_date_utc, status, error# error_number,
       sys_extract_utc(systimestamp) collected_at_utc
from sys.dba_scheduler_job_run_details
where status = 'FAILED'
with read only;
comment on table DB_HEALTH_AGENT.MONITOR_FAILED_JOBS is
'Failed Scheduler runs in retained logs visible in this container. Filter LOG_DATE for the requested window, e.g. SYSTIMESTAMP minus NUMTODSINTERVAL(48,''HOUR''). No rows does not prove successful execution. No fixed default time window.';

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
