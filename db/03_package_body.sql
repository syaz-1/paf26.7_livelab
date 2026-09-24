create or replace package body DB_HEALTH_OWNER.DB_HEALTH_API as
  function bounded_integer(p_value number, p_max number) return pls_integer is
  begin
    if p_value is null or p_value < 1 or p_value > p_max
       or p_value <> trunc(p_value) then
      raise_application_error(-20001, 'Parameter must be an integer in the documented range.');
    end if;
    return p_value;
  end;

  function response(p_check varchar2, p_source varchar2, p_rows json_array_t,
                    p_truncated boolean default false,
                    p_note varchar2 default null,
                    p_code number default 0) return clob is
    l_result json_object_t := json_object_t();
  begin
    l_result.put('api_version', '1');
    l_result.put('check', p_check);
    l_result.put('status', case when p_code = 0 then 'ok'
                               when p_code = -20001 then 'invalid_input'
                               else 'unavailable' end);
    l_result.put('database', sys_context('USERENV','DB_NAME'));
    l_result.put('container', sys_context('USERENV','CON_NAME'));
    l_result.put('collected_at_utc',
      to_char(sys_extract_utc(systimestamp), 'YYYY-MM-DD"T"HH24:MI:SS.FF3"Z"'));
    l_result.put('source', p_source);
    l_result.put('row_count', p_rows.get_size());
    l_result.put('truncated', p_truncated);
    l_result.put('rows', p_rows);
    l_result.put('note', p_note);
    if p_code <> 0 then
      l_result.put('error_code', p_code);
      l_result.put('message', case when p_code = -20001
        then 'Use integer p_limit 1..100 and p_hours_back 1..168; null is invalid.'
        else 'Collection failed. This check is unavailable; ask the DBA to investigate.' end);
    end if;
    return l_result.to_clob();
  end;

  function get_database_overview return clob is
    l_rows json_array_t := json_array_t();
    l_row json_object_t := json_object_t();
  begin
    l_row.put('reachable', true);
    l_row.put('session_user', sys_context('USERENV','SESSION_USER'));
    l_row.put('service_name', sys_context('USERENV','SERVICE_NAME'));
    l_row.put('cloud_service', sys_context('USERENV','CLOUD_SERVICE'));
    l_rows.append(l_row);
    return response('database_overview', 'SYS_CONTEXT(USERENV)', l_rows,
      p_note => 'A successful call proves this database session is reachable. It is not an overall health assessment.');
  exception when others then
    return response('database_overview', 'SYS_CONTEXT(USERENV)', json_array_t(), p_code => sqlcode);
  end;

  function get_sessions(p_limit number default 20) return clob is
    l_limit pls_integer;
    l_rows json_array_t := json_array_t();
    l_row json_object_t;
    l_truncated boolean := false;
  begin
    l_limit := bounded_integer(p_limit, 100);
    for r in (
      select inst_id, sid, serial#, status, username, sql_id, event, wait_class,
             state, seconds_in_wait, blocking_session_status, blocking_instance,
             blocking_session
      from sys.gv_$session
      where type = 'USER' and (status = 'ACTIVE' or blocking_session_status = 'VALID')
      order by case when blocking_session_status = 'VALID' then 0 else 1 end,
               seconds_in_wait desc, inst_id, sid
      fetch first (l_limit + 1) rows only
    ) loop
      if l_rows.get_size() = l_limit then l_truncated := true; exit; end if;
      l_row := json_object_t();
      l_row.put('instance_id', r.inst_id);
      l_row.put('sid', r.sid);
      l_row.put('serial_number', r.serial#);
      l_row.put('status', r.status);
      l_row.put('username', r.username);
      l_row.put('sql_id', r.sql_id);
      l_row.put('event', r.event);
      l_row.put('wait_class', r.wait_class);
      l_row.put('wait_state', r.state);
      l_row.put('seconds_in_wait', r.seconds_in_wait);
      l_row.put('blocking_session_status', r.blocking_session_status);
      if r.blocking_session_status = 'VALID' then
        l_row.put('blocking_instance_id', r.blocking_instance);
        l_row.put('blocking_sid', r.blocking_session);
      end if;
      l_rows.append(l_row);
    end loop;
    return response('sessions', 'SYS.GV_$SESSION', l_rows, l_truncated,
      'Current active or blocked user sessions visible in this container. Blocked sessions sort first. Interpret seconds_in_wait with wait_state; it is not always a current wait duration.');
  exception when others then
    return response('sessions', 'SYS.GV_$SESSION', json_array_t(), p_code => sqlcode);
  end;

  function get_storage_usage(p_limit number default 20) return clob is
    l_limit pls_integer;
    l_rows json_array_t := json_array_t();
    l_row json_object_t;
    l_truncated boolean := false;
  begin
    l_limit := bounded_integer(p_limit, 100);
    for r in (
      select m.tablespace_name, m.used_percent,
             m.used_space * t.block_size as used_bytes,
             m.tablespace_size * t.block_size as capacity_bytes
      from sys.dba_tablespace_usage_metrics m
      join sys.dba_tablespaces t on t.tablespace_name = m.tablespace_name
      order by m.used_percent desc nulls last, m.tablespace_name
      fetch first (l_limit + 1) rows only
    ) loop
      if l_rows.get_size() = l_limit then l_truncated := true; exit; end if;
      l_row := json_object_t();
      l_row.put('tablespace_name', r.tablespace_name);
      l_row.put('used_percent', round(r.used_percent, 2));
      l_row.put('used_bytes', r.used_bytes);
      l_row.put('capacity_bytes', r.capacity_bytes);
      l_rows.append(l_row);
    end loop;
    return response('storage_usage', 'SYS.DBA_TABLESPACE_USAGE_METRICS + SYS.DBA_TABLESPACES',
      l_rows, l_truncated,
      'Tablespace capacity reported by Oracle, including autoextend considerations. This is not Autonomous service provisioned storage or the OCI StorageUtilization metric.');
  exception when others then
    return response('storage_usage', 'SYS.DBA_TABLESPACE_USAGE_METRICS + SYS.DBA_TABLESPACES',
      json_array_t(), p_code => sqlcode);
  end;

  function get_failed_jobs(p_hours_back number default 24,
                           p_limit number default 20) return clob is
    l_limit pls_integer;
    l_hours pls_integer;
    l_rows json_array_t := json_array_t();
    l_row json_object_t;
    l_truncated boolean := false;
  begin
    l_limit := bounded_integer(p_limit, 100);
    l_hours := bounded_integer(p_hours_back, 168);
    for r in (
      select owner, job_name, log_id, log_date, status, error#
      from sys.dba_scheduler_job_run_details
      where status = 'FAILED'
        and log_date >= systimestamp - numtodsinterval(l_hours, 'HOUR')
      order by log_date desc, log_id desc
      fetch first (l_limit + 1) rows only
    ) loop
      if l_rows.get_size() = l_limit then l_truncated := true; exit; end if;
      l_row := json_object_t();
      l_row.put('owner', r.owner);
      l_row.put('job_name', r.job_name);
      l_row.put('log_id', r.log_id);
      l_row.put('log_date_utc',
        to_char(sys_extract_utc(r.log_date), 'YYYY-MM-DD"T"HH24:MI:SS.FF3"Z"'));
      l_row.put('status', r.status);
      l_row.put('error_number', r.error#);
      l_rows.append(l_row);
    end loop;
    return response('failed_jobs', 'SYS.DBA_SCHEDULER_JOB_RUN_DETAILS', l_rows, l_truncated,
      'FAILED runs in the last ' || to_char(l_hours, 'FM990')
      || ' hours, limited to retained scheduler logs visible in this container. No rows does not prove jobs ran successfully.');
  exception when others then
    return response('failed_jobs', 'SYS.DBA_SCHEDULER_JOB_RUN_DETAILS', json_array_t(), p_code => sqlcode);
  end;

  function get_sql_workload(p_limit number default 20) return clob is
    l_limit pls_integer;
    l_rows json_array_t := json_array_t();
    l_row json_object_t;
    l_truncated boolean := false;
  begin
    l_limit := bounded_integer(p_limit, 100);
    for r in (
      select inst_id, sql_id, plan_hash_value, executions, elapsed_time, cpu_time,
             buffer_gets, disk_reads, rows_processed
      from sys.gv_$sqlstats
      where executions > 0
      order by elapsed_time desc, inst_id, sql_id, plan_hash_value
      fetch first (l_limit + 1) rows only
    ) loop
      if l_rows.get_size() = l_limit then l_truncated := true; exit; end if;
      l_row := json_object_t();
      l_row.put('instance_id', r.inst_id);
      l_row.put('sql_id', r.sql_id);
      l_row.put('plan_hash_value', r.plan_hash_value);
      l_row.put('executions', r.executions);
      l_row.put('elapsed_seconds', round(r.elapsed_time / 1000000, 6));
      l_row.put('cpu_seconds', round(r.cpu_time / 1000000, 6));
      l_row.put('average_elapsed_seconds', round(r.elapsed_time / r.executions / 1000000, 6));
      l_row.put('buffer_gets', r.buffer_gets);
      l_row.put('disk_reads', r.disk_reads);
      l_row.put('rows_processed', r.rows_processed);
      l_rows.append(l_row);
    end loop;
    return response('sql_workload', 'SYS.GV_$SQLSTATS', l_rows, l_truncated,
      'Cumulative cached statistics per instance and SQL entry, ordered by total elapsed time. Not a last-N-hours report or a measure of single-execution latency. SQL text and bind values are omitted.');
  exception when others then
    return response('sql_workload', 'SYS.GV_$SQLSTATS', json_array_t(), p_code => sqlcode);
  end;
end DB_HEALTH_API;
/
