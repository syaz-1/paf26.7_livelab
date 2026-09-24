-- All retained Scheduler run statuses for the Select AI monitoring MVP.
whenever sqlerror exit failure rollback
begin
  if sys_context('USERENV','SESSION_USER') <> 'ADMIN'
     or sys_context('USERENV','DB_NAME') <> 'G2C3435895384DA_DEMO' then
    raise_application_error(-20030, 'Unexpected database or session user; stopping.');
  end if;
end;
/
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
