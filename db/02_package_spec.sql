create or replace package DB_HEALTH_OWNER.DB_HEALTH_API authid definer as
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
