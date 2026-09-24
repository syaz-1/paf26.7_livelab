-- Run as DB_HEALTH_AGENT, never as ADMIN or via ALTER SESSION SET CURRENT_SCHEMA.
declare
  l_doc json_object_t;
  l_rows json_array_t;
  l_row json_object_t;
  l_count number;
  procedure require(p_true boolean, p_label varchar2) is
  begin
    if p_true is null or not p_true then raise_application_error(-20041, p_label); end if;
    dbms_output.put_line('PASS: ' || p_label);
  end;
  procedure check_result(p_json clob, p_check varchar2, p_limit number) is
  begin
    l_doc := json_object_t.parse(p_json);
    l_rows := l_doc.get_array('rows');
    require(l_doc.get_string('status') = 'ok', p_check || ' collection succeeds');
    require(l_doc.get_string('check') = p_check, p_check || ' check identity');
    require(l_doc.get_string('database') = sys_context('USERENV','DB_NAME'), p_check || ' database identity');
    require(l_doc.get_string('collected_at_utc') is not null, p_check || ' timestamp');
    require(l_doc.get_number('row_count') = l_rows.get_size()
      and l_rows.get_size() <= p_limit, p_check || ' bounded row count');
    require(dbms_lob.instr(lower(p_json), 'sql_text') = 0
      and dbms_lob.instr(lower(p_json), 'sql_fulltext') = 0, p_check || ' no SQL text field');
  end;
  procedure invalid(p_json clob, p_label varchar2) is
    l_error json_object_t := json_object_t.parse(p_json);
  begin
    require(l_error.get_string('status') = 'invalid_input'
      and l_error.get_number('row_count') = 0, p_label);
  end;
  procedure denied(p_sql varchar2, p_label varchar2) is
    l_value number;
  begin
    begin
      execute immediate p_sql into l_value;
    exception when others then
      if sqlcode in (-942, -1031) then
        dbms_output.put_line('PASS: ' || p_label);
        return;
      end if;
      raise;
    end;
    raise_application_error(-20042, 'Unexpected direct access: ' || p_label);
  end;
begin
  require(sys_context('USERENV','SESSION_USER') = 'DB_HEALTH_AGENT', 'Actual runtime login');
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_database_overview(), 'database_overview', 1);
  l_row := treat(l_rows.get(0) as json_object_t);
  require(l_row.get_string('session_user') = 'DB_HEALTH_AGENT', 'Package reports caller identity');
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_sessions(), 'sessions', 20);
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_storage_usage(), 'storage_usage', 20);
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(), 'failed_jobs', 20);
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_sql_workload(), 'sql_workload', 20);
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_sql_workload(1), 'sql_workload', 1);
  -- Seed no workloads: only assert truncation when this database has >= 2 entries.
  declare
    l_one json_object_t := l_doc;
    l_two json_object_t := json_object_t.parse(DB_HEALTH_AGENT.DB_HEALTH_API.get_sql_workload(2));
  begin
    if l_two.get_number('row_count') = 2 then
      require(l_one.get_boolean('truncated'), 'Truncation is reported when more rows exist');
    else
      dbms_output.put_line('SKIP: truncation fixture unavailable');
    end if;
  end;
  check_result(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(168, 100), 'failed_jobs', 100);
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_sessions(0), 'Reject zero limit');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_storage_usage(101), 'Reject over-limit');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_sql_workload(1.5), 'Reject fractional limit');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_sql_workload(null), 'Reject null limit');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(0), 'Reject zero history window');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(169), 'Reject excessive history window');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(null), 'Reject null history window');
  invalid(DB_HEALTH_AGENT.DB_HEALTH_API.get_failed_jobs(1.5), 'Reject fractional history window');
  denied('select count(*) from sys.gv_$session where 1=0', 'No direct session-view access');
  denied('select count(*) from sys.gv_$sqlstats where 1=0', 'No direct SQL-statistics access');
  denied('select count(*) from sys.dba_scheduler_job_run_details where 1=0', 'No direct scheduler-history access');
  select count(*) into l_count from session_privs
    where privilege in ('CREATE TABLE', 'CREATE PROCEDURE', 'ALTER SYSTEM', 'SELECT ANY DICTIONARY', 'SELECT ANY TABLE');
  require(l_count = 0, 'No create, administration or broad read system privileges');
  select count(*) into l_count from all_procedures
    where owner = 'DB_HEALTH_AGENT' and object_name = 'DB_HEALTH_API' and procedure_name is not null;
  require(l_count = 5, 'All five same-schema routines discoverable by runtime account');
  select count(*) into l_count from all_arguments
    where owner = 'DB_HEALTH_AGENT' and package_name = 'DB_HEALTH_API'
      and position = 0 and data_type = 'CLOB';
  require(l_count = 5, 'All five CLOB return signatures discoverable');
  select count(*) into l_count from user_procedures
    where object_name = 'DB_HEALTH_API' and procedure_name is not null;
  require(l_count = 5, 'All five wrappers visible in USER_PROCEDURES');
end;
/
