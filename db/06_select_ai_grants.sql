-- PROPOSED ONLY: requires explicit approval before execution.
-- Broad package capabilities extend beyond the fixed DB_HEALTH_API interface.
-- DBMS_CLOUD: database credential management and other cloud operations.
-- DBMS_CLOUD_AI: profile management and AI-generated query execution.
-- No monitoring SELECT grants or ACL/vector/team administration included.
whenever sqlerror exit failure rollback
begin
  if sys_context('USERENV','SESSION_USER') <> 'ADMIN'
     or sys_context('USERENV','DB_NAME') <> 'G2C3435895384DA_DEMO' then
    raise_application_error(-20030, 'Unexpected database or session user; stopping.');
  end if;
end;
/
grant execute on DBMS_CLOUD to DB_HEALTH_AGENT;
grant execute on DBMS_CLOUD_AI to DB_HEALTH_AGENT;
