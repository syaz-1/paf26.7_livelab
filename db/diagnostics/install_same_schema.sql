-- One-function package in the connection schema to test owner-only discovery.
-- Run as ADMIN using the target-checked SQLcl helper. Do not replace existing objects.
declare
  n number;
begin
  select count(*) into n from dba_objects
  where owner = 'DB_HEALTH_AGENT' and object_name = 'DB_HEALTH_API';
  if n <> 0 then
    raise_application_error(-20050, 'DB_HEALTH_AGENT.DB_HEALTH_API already exists; inspect before replacing.');
  end if;
end;
/

create package DB_HEALTH_AGENT.DB_HEALTH_API authid definer as
  function get_database_overview return clob;
end DB_HEALTH_API;
/

create package body DB_HEALTH_AGENT.DB_HEALTH_API as
  function get_database_overview return clob is
  begin
    return DB_HEALTH_OWNER.DB_HEALTH_API.get_database_overview();
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
    raise_application_error(-20051, 'Same-schema test package did not compile.');
  end if;
  dbms_output.put_line('PASS: same-schema test package compiled; no new grants required');
end;
/
