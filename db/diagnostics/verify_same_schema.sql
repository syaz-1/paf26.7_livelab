-- Run as DB_HEALTH_AGENT, not ADMIN.
select object_name, procedure_name, authid
from user_procedures
where object_name = 'DB_HEALTH_API' and procedure_name is not null;

declare
  n number;
  doc json_object_t;
  rows_ json_array_t;
  row_ json_object_t;
begin
  if sys_context('USERENV','SESSION_USER') <> 'DB_HEALTH_AGENT' then
    raise_application_error(-20052, 'Expected actual runtime login.');
  end if;
  select count(*) into n from user_procedures
  where object_name = 'DB_HEALTH_API' and procedure_name = 'GET_DATABASE_OVERVIEW';
  if n <> 1 then raise_application_error(-20053, 'Not visible in USER_PROCEDURES.'); end if;
  dbms_output.put_line('PASS: test function visible in USER_PROCEDURES');
  select count(*) into n from user_arguments
  where package_name = 'DB_HEALTH_API' and object_name = 'GET_DATABASE_OVERVIEW'
    and position = 0 and data_type = 'CLOB';
  if n <> 1 then raise_application_error(-20054, 'Return signature not visible.'); end if;
  dbms_output.put_line('PASS: CLOB signature visible in USER_ARGUMENTS');
  doc := json_object_t.parse(DB_HEALTH_AGENT.DB_HEALTH_API.get_database_overview());
  if doc.get_string('status') is null or doc.get_string('status') <> 'ok'
     or doc.get_number('row_count') is null or doc.get_number('row_count') <> 1 then
    raise_application_error(-20055, 'Test function did not return a successful result.');
  end if;
  rows_ := doc.get_array('rows');
  row_ := treat(rows_.get(0) as json_object_t);
  if row_.get_string('session_user') is null or row_.get_string('session_user') <> 'DB_HEALTH_AGENT' then
    raise_application_error(-20056, 'Unexpected reported caller.');
  end if;
  dbms_output.put_line('PASS: wrapper calls owner package and returns overview as runtime user');
end;
/
