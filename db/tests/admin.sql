declare
  l_count number;
  procedure require(p_true boolean, p_label varchar2) is
  begin
    if p_true is null or not p_true then raise_application_error(-20040, p_label); end if;
    dbms_output.put_line('PASS: ' || p_label);
  end;
begin
  select count(*) into l_count from dba_users
  where username = 'DB_HEALTH_OWNER' and authentication_type = 'NONE';
  require(l_count = 1, 'Owner has no login credential');

  select count(*) into l_count from dba_users
  where username = 'DB_HEALTH_AGENT' and authentication_type = 'PASSWORD' and account_status = 'OPEN';
  require(l_count = 1, 'Runtime account has password authentication and is open');

  select count(*) into l_count from dba_sys_privs
  where grantee in ('DB_HEALTH_OWNER', 'DB_HEALTH_AGENT')
    and not (grantee = 'DB_HEALTH_AGENT' and privilege = 'CREATE SESSION' and admin_option = 'NO');
  require(l_count = 0, 'No unexpected direct system privileges');

  select count(*) into l_count from dba_sys_privs
  where grantee = 'DB_HEALTH_AGENT' and privilege = 'CREATE SESSION';
  require(l_count = 1, 'Runtime has CREATE SESSION');

  select count(*) into l_count from dba_role_privs
  where grantee in ('DB_HEALTH_OWNER', 'DB_HEALTH_AGENT');
  require(l_count = 0, 'Neither monitoring account has roles');

  select count(*) into l_count from dba_tab_privs
  where grantee = 'DB_HEALTH_OWNER';
  require(l_count = 5, 'Owner has exactly five direct object grants');

  select count(*) into l_count from dba_tab_privs
  where grantee = 'DB_HEALTH_OWNER' and owner = 'SYS' and privilege = 'SELECT'
    and grantable = 'NO' and table_name in ('GV_$SESSION', 'GV_$SQLSTATS',
      'DBA_TABLESPACE_USAGE_METRICS', 'DBA_TABLESPACES', 'DBA_SCHEDULER_JOB_RUN_DETAILS');
  require(l_count = 5, 'Owner can read only the five approved monitoring sources through direct grants');

  select count(*) into l_count from dba_tab_privs where grantee = 'DB_HEALTH_AGENT';
  require(l_count = 1, 'Runtime has exactly one direct object grant');
  select count(*) into l_count from dba_tab_privs
  where grantee = 'DB_HEALTH_AGENT' and owner = 'DB_HEALTH_OWNER'
    and table_name = 'DB_HEALTH_API' and privilege = 'EXECUTE' and grantable = 'NO';
  require(l_count = 1, 'Runtime can execute only the health package through direct grants');

  select count(*) into l_count from dba_objects
  where owner = 'DB_HEALTH_OWNER' and object_name = 'DB_HEALTH_API'
    and object_type in ('PACKAGE', 'PACKAGE BODY') and status = 'VALID';
  require(l_count = 2, 'Package specification and body are valid');
  select count(*) into l_count from dba_procedures
  where owner = 'DB_HEALTH_OWNER' and object_name = 'DB_HEALTH_API'
    and procedure_name is not null and authid = 'DEFINER';
  require(l_count = 5, 'Exactly five public definer-rights routines');
end;
/

-- Independent source comparisons. Live storage values may change between reads;
-- if that happens, inspect the change and rerun this read-only verification.
declare
  doc json_object_t;
  rows_ json_array_t;
  row_ json_object_t;
  name_ varchar2(128);
  used_ number;
  capacity_ number;
  count_ number;
  elapsed_ number;
  executions_ number;
  id_ varchar2(13);
  instance_ number;
  plan_ number;
  procedure require(ok boolean, label_ varchar2) is
  begin
    if ok is null or not ok then raise_application_error(-20043, label_); end if;
    dbms_output.put_line('PASS: ' || label_);
  end;
begin
  doc := json_object_t.parse(DB_HEALTH_OWNER.DB_HEALTH_API.get_storage_usage(100));
  require(doc.get_string('status') = 'ok', 'Storage source comparison available');
  rows_ := doc.get_array('rows');
  if rows_.get_size() > 0 then
    for i in 0 .. rows_.get_size() - 1 loop
      row_ := treat(rows_.get(i) as json_object_t);
      name_ := row_.get_string('tablespace_name');
      select m.used_space * t.block_size, m.tablespace_size * t.block_size
        into used_, capacity_
        from sys.dba_tablespace_usage_metrics m
        join sys.dba_tablespaces t on t.tablespace_name = m.tablespace_name
        where m.tablespace_name = name_;
      require(row_.get_number('used_bytes') = used_
          and row_.get_number('capacity_bytes') = capacity_,
          'Storage bytes match independent source calculation');
    end loop;
  else
    dbms_output.put_line('SKIP: no storage metrics available for comparison');
  end if;
  doc := json_object_t.parse(DB_HEALTH_OWNER.DB_HEALTH_API.get_sql_workload(1));
  require(doc.get_string('status') = 'ok', 'SQL source comparison available');
  rows_ := doc.get_array('rows');
  if rows_.get_size() > 0 then
    row_ := treat(rows_.get(0) as json_object_t);
    id_ := row_.get_string('sql_id');
    instance_ := row_.get_number('instance_id');
    plan_ := row_.get_number('plan_hash_value');
    select elapsed_time / 1000000, executions into elapsed_, executions_
      from sys.gv_$sqlstats
      where sql_id = id_ and inst_id = instance_ and plan_hash_value = plan_;
    require(row_.get_number('elapsed_seconds') <= elapsed_
        and row_.get_number('executions') <= executions_,
        'SQL elapsed seconds and executions agree with live source counters');
    require(abs(row_.get_number('average_elapsed_seconds')
        - row_.get_number('elapsed_seconds') / row_.get_number('executions')) < 0.000002,
        'SQL average is expressed in seconds per execution');
  else
    dbms_output.put_line('SKIP: no SQL metrics available for comparison');
  end if;
  doc := json_object_t.parse(DB_HEALTH_OWNER.DB_HEALTH_API.get_failed_jobs(24, 100));
  require(doc.get_string('status') = 'ok', 'Job source comparison available');
  rows_ := doc.get_array('rows');
  if rows_.get_size() = 0 then
    select count(*) into count_ from sys.dba_scheduler_job_run_details
      where status = 'FAILED' and log_date >= systimestamp - interval '24' hour;
    require(count_ = 0, 'Empty job result matches independent source query');
  else
    for i in 0 .. rows_.get_size() - 1 loop
      row_ := treat(rows_.get(i) as json_object_t);
      used_ := row_.get_number('log_id');
      select count(*) into count_ from sys.dba_scheduler_job_run_details
        where log_id = used_ and status = 'FAILED';
      require(count_ = 1, 'Failed job exists in independent source query');
    end loop;
  end if;
end;
/
