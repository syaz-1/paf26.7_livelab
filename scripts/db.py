#!/usr/bin/env python3
"""Run the phase-one SQL through the prescribed SQLcl, without CLI passwords."""
import argparse
import os
from pathlib import Path
import re
import secrets
import string
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SQLCL = Path('/home/syazwan/.vscode-server/extensions/oracle.sql-developer-26.2.1-linux-x64/dbtools/sqlcl/bin/sql')
PRIVATE = ROOT / '.local'
PASSWORD = PRIVATE / 'db_health_agent.password'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'provision', 'install', 'verify-admin', 'verify-runtime', 'install-discovery-test', 'verify-discovery-test', 'install-runtime-api'))
    parser.add_argument('--connection', required=True, help='Existing saved SQLcl connection name')
    parser.add_argument('--expected-db', required=True, help='Exact SYS_CONTEXT(USERENV, DB_NAME) value')
    args = parser.parse_args()
    if any(c in args.connection for c in '\r\n"'):
        parser.error('Connection name cannot contain quotes or line breaks.')
    if not re.fullmatch(r'[A-Za-z0-9_$#]+', args.expected_db):
        parser.error('Expected database name must be an Oracle identifier.')
    if not SQLCL.is_file():
        parser.error(f'SQLcl not found: {SQLCL}')

    password = None
    if args.action == 'provision':
        PRIVATE.mkdir(mode=0o700, exist_ok=True)
        PRIVATE.chmod(0o700)
        password = 'Aa9!' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
        try:
            fd = os.open(PASSWORD, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            parser.error('Credential file already exists. Inspect prior provisioning; do not reset it automatically.')
        with os.fdopen(fd, 'w') as stream:
            stream.write(password + '\n')
    elif args.action in ('verify-runtime', 'verify-discovery-test'):
        password = PASSWORD.read_text().strip()
        if not re.fullmatch(r'[A-Za-z0-9!_-]{24,64}', password):
            parser.error('Unexpected credential format.')

    lines = [
        'set echo off', 'set verify off', 'set define off', 'set history off',
        'whenever sqlerror exit failure rollback',
        'whenever oserror exit failure rollback',
        f'connect -name "{args.connection}"',
    ]
    # Supply CONNECT's password option over private stdin: SQLcl's masked
    # password prompt requires a terminal and cannot reliably consume piped input.
    # History is disabled before CONNECT. The secret never enters process argv.
    if args.action in ('verify-runtime', 'verify-discovery-test'):
        lines[-1] = f'connect -name "{args.connection}" -password "{password}"'
    expected_user = 'DB_HEALTH_AGENT' if args.action in ('verify-runtime', 'verify-discovery-test') else 'ADMIN'
    lines.extend([
        'set serveroutput on size unlimited', 'set sqlformat ansiconsole',
        'set feedback off',
        'begin',
        f"  if sys_context('USERENV','DB_NAME') <> '{args.expected_db}'",
        f"     or sys_context('USERENV','SESSION_USER') <> '{expected_user}' then",
        "    raise_application_error(-20030, 'Unexpected database or session user; stopping.');",
        '  end if;', 'end;', '/',
    ])
    if args.action == 'provision':
        lines.extend([
            '@db/00_preflight.sql',
            'variable agent_password varchar2(128)',
            f"begin :agent_password := '{password}'; end;", '/',
            'clear buffer', '@db/01_provision.sql',
        ])
    elif args.action == 'install':
        lines.extend(['@db/02_package_spec.sql', '@db/03_package_body.sql', '@db/04_validate_install.sql', '@db/05_runtime_api.sql'])
    elif args.action == 'install-runtime-api':
        lines.append('@db/05_runtime_api.sql')
    elif args.action == 'preflight':
        lines.append('@db/00_preflight.sql')
    elif args.action == 'install-discovery-test':
        lines.append('@db/diagnostics/install_same_schema.sql')
    elif args.action == 'verify-discovery-test':
        lines.append('@db/diagnostics/verify_same_schema.sql')
    elif args.action == 'verify-admin':
        lines.append('@db/tests/admin.sql')
    else:
        lines.append('@db/tests/runtime.sql')
    lines.extend(['clear buffer', 'exit success rollback'])
    try:
        result = subprocess.run(
            [str(SQLCL), '-s', '/nolog'], input='\n'.join(lines) + '\n',
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        # Do not display captured stdin/partial output, which may include secrets.
        print('SQLcl timed out. Inspect database state before retrying; Oracle DDL is not transactional.', file=sys.stderr)
        return 1
    output = result.stdout.replace(password, '[REDACTED]') if password else result.stdout
    print(output, end='')
    # WHENEVER SQLERROR does not catch all SQLcl client errors.
    client_error = re.search(r'(?m)(?:ORA-\d{5}|SP2-\d+|Unknown Command|Error starting at line)', output)
    if result.returncode or client_error:
        print('Step failed. Earlier DDL may have committed; inspect before retrying.', file=sys.stderr)
        return 1
    print(f'{args.action}: PASS')
    if args.action == 'provision':
        print('Runtime credential saved to .local/db_health_agent.password (mode 0600).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
