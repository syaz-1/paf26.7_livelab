-- Explicitly approved existing monitoring views for the Select AI pilot.
-- Direct SELECT exposes all columns in these views; no catalog role or grant option.
whenever sqlerror exit failure rollback
begin
  if sys_context('USERENV','SESSION_USER') <> 'ADMIN'
     or sys_context('USERENV','DB_NAME') <> 'G2C3435895384DA_DEMO' then
    raise_application_error(-20030, 'Unexpected database or session user; stopping.');
  end if;
end;
/
grant select on SYS.GV_$SESSION to DB_HEALTH_AGENT;
grant select on SYS.GV_$SQLSTATS to DB_HEALTH_AGENT;
grant select on SYS.DBA_TABLESPACE_USAGE_METRICS to DB_HEALTH_AGENT;
grant select on SYS.DBA_TABLESPACES to DB_HEALTH_AGENT;
grant select on SYS.DBA_SCHEDULER_JOB_RUN_DETAILS to DB_HEALTH_AGENT;
