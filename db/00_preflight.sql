-- Read-only; run as the provisioning account.
select sys_context('USERENV','SESSION_USER') as session_user,
       sys_context('USERENV','DB_NAME') as db_name,
       sys_context('USERENV','CON_NAME') as container_name,
       sys_context('USERENV','CLOUD_SERVICE') as cloud_service
from dual;

select banner_full from v$version;

select username, authentication_type, account_status
from dba_users
where username in ('DB_HEALTH_OWNER', 'DB_HEALTH_AGENT');

-- Validate the exact columns used by the package without reading workload data.
select inst_id, sid, serial#, status, username, sql_id, event, wait_class,
       state, seconds_in_wait, blocking_session_status, blocking_instance,
       blocking_session, type
from sys.gv_$session where 1 = 0;

select inst_id, sql_id, plan_hash_value, executions, elapsed_time, cpu_time,
       buffer_gets, disk_reads, rows_processed
from sys.gv_$sqlstats where 1 = 0;

select m.tablespace_name, m.used_space, m.tablespace_size, m.used_percent,
       t.block_size
from sys.dba_tablespace_usage_metrics m
join sys.dba_tablespaces t on t.tablespace_name = m.tablespace_name
where 1 = 0;

select owner, job_name, log_id, log_date, status, error#
from sys.dba_scheduler_job_run_details where 1 = 0;
