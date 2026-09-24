-- Input: :agent_password VARCHAR2 bind populated by scripts/db.py.
-- First installation only. Never adopt, replace, unlock or reset existing users.
declare
  l_count number;
begin
  select count(*) into l_count from dba_users
  where username in ('DB_HEALTH_OWNER', 'DB_HEALTH_AGENT');
  if l_count <> 0 then
    raise_application_error(-20010, 'Monitoring users already exist; inspect before resuming.');
  end if;
  if :agent_password is null
     or not regexp_like(:agent_password, '^[A-Za-z0-9!_-]{24,64}$') then
    raise_application_error(-20011, 'Missing or invalid generated runtime password.');
  end if;
  execute immediate 'create user DB_HEALTH_OWNER no authentication';
  execute immediate 'create user DB_HEALTH_AGENT identified by "'
                    || :agent_password || '"';
  :agent_password := null;
end;
/

grant create session to DB_HEALTH_AGENT;

-- Direct grants are required by the definer-rights package. No catalog roles.
grant select on sys.gv_$session to DB_HEALTH_OWNER;
grant select on sys.gv_$sqlstats to DB_HEALTH_OWNER;
grant select on sys.dba_tablespace_usage_metrics to DB_HEALTH_OWNER;
grant select on sys.dba_tablespaces to DB_HEALTH_OWNER;
grant select on sys.dba_scheduler_job_run_details to DB_HEALTH_OWNER;

-- ADMIN deploys the package into DB_HEALTH_OWNER. Neither new user needs
-- CREATE PROCEDURE, CREATE TABLE, quotas, ANY privileges or administrative roles.
