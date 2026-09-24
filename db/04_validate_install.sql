-- Run as ADMIN after compiling. Compilation warnings must fail deployment.
select type, line, position, text
from dba_errors
where owner = 'DB_HEALTH_OWNER' and name = 'DB_HEALTH_API'
order by sequence;

declare
  l_count number;
begin
  select count(*) into l_count from dba_objects
  where owner = 'DB_HEALTH_OWNER' and object_name = 'DB_HEALTH_API'
    and object_type in ('PACKAGE', 'PACKAGE BODY') and status = 'VALID';
  if l_count <> 2 then
    raise_application_error(-20020, 'Monitoring package did not compile.');
  end if;
end;
/

grant execute on DB_HEALTH_OWNER.DB_HEALTH_API to DB_HEALTH_AGENT;
