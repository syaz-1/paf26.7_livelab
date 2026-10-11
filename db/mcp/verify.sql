set history off
set serveroutput on
set verify off
set define on
whenever sqlerror exit failure rollback
begin
  if user <> 'DB_HEALTH_AGENT' or sys_context('USERENV','DB_NAME') <> '&1' then
    raise_application_error(-20030,'Unexpected runtime identity.');
  end if;
end;
/
set define off
declare
  j json_object_t;
  procedure expect(value varchar2, wanted varchar2) is
  begin
    if value is null or value<>wanted then raise_application_error(-20040,'Diagnostic assertion failed.'); end if;
  end;
begin
  j:=json_object_t.parse(MCP_LOGIN_RUNBOOK()); expect(j.get_string('runbook_id'),'ADB-LOGIN-001');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS('PAF_MCP_DEMO')); expect(j.get_string('account_status'),'LOCKED');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS('DB_HEALTH_AGENT')); expect(j.get_string('account_status'),'OPEN');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS('PAF_MCP_MISSING')); expect(j.get_string('status'),'not_found');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS('ADMIN')); expect(j.get_string('status'),'invalid_input');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS(null)); expect(j.get_string('status'),'invalid_input');
  j:=json_object_t.parse(MCP_ACCOUNT_STATUS(q'[PAF_MCP_DEMO' OR '1'='1]')); expect(j.get_string('status'),'invalid_input');
  j:=json_object_t.parse(MCP_LOGIN_PRIVILEGES('PAF_MCP_DEMO')); expect(to_char(j.get_number('direct_create_session')),'1');
  j:=json_object_t.parse(MCP_LOGIN_PRIVILEGES('ADMIN')); expect(j.get_string('status'),'invalid_input');
  dbms_output.put_line('PASS: runbook, locked/open/missing accounts, direct login grant, scope and injection checks.');
end;
/
