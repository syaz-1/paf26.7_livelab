-- Run as DB_HEALTH_AGENT using SQLcl. Bounded reads; no model calls.
set echo off
set verify off
set history off
set define on
whenever sqlerror exit failure rollback
begin
  if sys_context('USERENV','SESSION_USER') <> 'DB_HEALTH_AGENT'
     or sys_context('USERENV','DB_NAME') <> '&1' then
    raise_application_error(-20030,'Unexpected database or login; stopping.');
  end if;
end;
/
set define off
select user as session_user, sys_context('USERENV','DB_NAME') as database_name from dual;
select o.object_name, o.status, v.read_only
from user_objects o join user_views v on v.view_name=o.object_name
where o.object_type='VIEW' and o.object_name in
 ('MONITOR_DATABASE_OVERVIEW','MONITOR_SESSIONS','MONITOR_STORAGE_USAGE',
  'MONITOR_SQL_WORKLOAD','MONITOR_JOB_RUNS')
order by o.object_name;
select database_name, service_name, collected_at_utc from MONITOR_DATABASE_OVERVIEW;
select instance_id, sid, status, blocking_session_status
from MONITOR_SESSIONS fetch first 5 rows only;
select tablespace_name, used_percent from MONITOR_STORAGE_USAGE
order by used_percent desc fetch first 5 rows only;
select job_name, status, log_date_utc from MONITOR_JOB_RUNS
order by log_date_utc desc fetch first 5 rows only;
select sql_id, executions, elapsed_seconds from MONITOR_SQL_WORKLOAD
order by elapsed_seconds desc fetch first 5 rows only;
