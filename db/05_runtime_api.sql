-- Same-schema facade for Agent Factory discovery. Deploy as ADMIN.
-- Uses the existing EXECUTE grant; adds no system or monitoring-view privileges.
create or replace package DB_HEALTH_AGENT.DB_HEALTH_API authid definer as
  -- All functions return a JSON CLOB; status is ok, invalid_input or unavailable.
  -- An ok result means collection succeeded, not that the database is healthy.
  function get_database_overview return clob;
  function get_sessions(p_limit number default 20) return clob;
  function get_storage_usage(p_limit number default 20) return clob;
  function get_failed_jobs(p_hours_back number default 24,
                           p_limit number default 20) return clob;
  function get_sql_workload(p_limit number default 20) return clob;
end DB_HEALTH_API;
/

create or replace package body DB_HEALTH_AGENT.DB_HEALTH_API as
  function get_database_overview return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_database_overview();
  end;
  function get_sessions(p_limit number default 20) return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_sessions(p_limit);
  end;
  function get_storage_usage(p_limit number default 20) return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_storage_usage(p_limit);
  end;
  function get_failed_jobs(p_hours_back number default 24,
                           p_limit number default 20) return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_failed_jobs(p_hours_back, p_limit);
  end;
  function get_sql_workload(p_limit number default 20) return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_sql_workload(p_limit);
  end;
end DB_HEALTH_API;
/

select type, line, position, text from dba_errors
where owner = 'DB_HEALTH_AGENT' and name = 'DB_HEALTH_API'
order by sequence;

declare
  n number;
begin
  select count(*) into n from dba_objects
  where owner = 'DB_HEALTH_AGENT' and object_name = 'DB_HEALTH_API'
    and object_type in ('PACKAGE', 'PACKAGE BODY') and status = 'VALID';
  if n <> 2 then
    raise_application_error(-20057, 'Runtime wrapper package did not compile.');
  end if;
  dbms_output.put_line('PASS: five-function runtime wrapper package compiled');
end;
/
