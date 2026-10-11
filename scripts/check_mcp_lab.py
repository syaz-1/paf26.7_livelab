#!/usr/bin/env python3
"""Test the three read-only DBA lab tools over managed ADB MCP; no model calls."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

from db import SQLCL, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connection', required=True, help='Saved ADMIN SQLcl connection')
    parser.add_argument('--expected-db', required=True)
    parser.add_argument('--private-dir', type=Path, required=True)
    args = parser.parse_args()
    if any(c in args.connection for c in '\r\n"'):
        parser.error('Invalid connection name')
    commands = '\n'.join([
        'set echo off', 'set history off', 'set sqlformat json',
        'whenever sqlerror exit failure rollback',
        f'connect -name "{args.connection}"',
        "select user session_user, sys_context('USERENV','DB_NAME') db_name, cloud_identity from v$pdbs;",
        'exit rollback', '',
    ])
    try:
        query = subprocess.run([str(SQLCL), '-s', '/nolog'], input=commands,
                               cwd=ROOT, text=True, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        raise RuntimeError('SQLcl metadata query timed out; output withheld.') from None
    if query.returncode or re.search(r'ORA-\d{5}|SP2-\d+', query.stdout):
        raise RuntimeError('SQLcl metadata query failed; output withheld.')
    start = query.stdout.find('{"results"')
    metadata, _ = json.JSONDecoder().raw_decode(query.stdout[start:])
    row = metadata['results'][0]['items'][0]
    if row['db_name'] != args.expected_db or row['session_user'] != 'ADMIN':
        raise RuntimeError('Unexpected database or provisioning identity.')
    identity = row['cloud_identity']
    if isinstance(identity, str):
        identity = json.loads(identity)
    region, ocid = identity['REGION'], identity['DATABASE_OCID'].lower()
    if not re.fullmatch(r'[a-z0-9-]+', region) or not re.fullmatch(r'ocid1\.autonomousdatabase\.[a-z0-9.-]+', ocid):
        raise RuntimeError('Unexpected cloud identity.')
    # This workshop uses the public regional endpoint. Private endpoints require
    # a separately reviewed hostname/network configuration.
    base = f'https://dataaccess.adb.{region}.oraclecloudapps.com/adb'
    password = (args.private_dir / 'db_health_agent.password').read_text().strip()
    request = urllib.request.Request(
        f'{base}/auth/v1/databases/{ocid}/token',
        data=json.dumps({'grant_type': 'password', 'username': 'DB_HEALTH_AGENT',
                         'password': password}).encode(),
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        token = json.load(response)['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
               'Accept': 'application/json, text/event-stream'}
    next_id = 0

    def call(method, params=None, notification=False):
        nonlocal next_id
        next_id += 1
        payload = {'jsonrpc': '2.0', 'method': method}
        if not notification:
            payload['id'] = next_id
        if params is not None:
            payload['params'] = params
        request = urllib.request.Request(f'{base}/mcp/v1/databases/{ocid}',
                                         data=json.dumps(payload).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.headers.get('Mcp-Session-Id'):
                headers['Mcp-Session-Id'] = response.headers['Mcp-Session-Id']
            raw = response.read().decode()
        if not raw.strip():
            return {}
        if raw.lstrip().startswith('{'):
            parsed = json.loads(raw)
        else:
            events = [json.loads(line[5:].strip()) for line in raw.splitlines()
                      if line.startswith('data:')]
            parsed = next((event for event in events if event.get('id') == payload.get('id')), {})
        if 'error' in parsed:
            raise RuntimeError(f'{method} returned a JSON-RPC error; response withheld.')
        if not notification and 'result' not in parsed:
            raise RuntimeError(f'{method} returned no result.')
        return parsed.get('result', {})

    initialized = call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                      'clientInfo': {'name': 'paf-dba-lab-check', 'version': '1.0'}})
    headers['MCP-Protocol-Version'] = initialized['protocolVersion']
    notification_ok = True
    try:
        call('notifications/initialized', notification=True)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise
        notification_ok = False
        print('WARNING: initialized notification returned HTTP 403; testing direct requests only.')
    tools = []
    params = {}
    while True:
        page = call('tools/list', params)
        tools.extend(page.get('tools', []))
        if not page.get('nextCursor'):
            break
        params = {'cursor': page['nextCursor']}
    expected = {'MCP_LOGIN_RUNBOOK', 'MCP_ACCOUNT_STATUS', 'MCP_LOGIN_PRIVILEGES'}
    names = {tool['name'] for tool in tools}
    if not expected.issubset(names):
        raise RuntimeError('Missing lab tools: ' + ', '.join(sorted(expected - names)))
    print('PASS: all three lab tools discovered')
    if names - expected:
        print('WARNING: additional tools are exposed; restrict PAF selection to the three lab tools.')
    cases = [
        ('MCP_LOGIN_RUNBOOK', {}, 'runbook_id', 'ADB-LOGIN-001'),
        ('MCP_ACCOUNT_STATUS', {'p_username': 'PAF_MCP_DEMO'}, 'account_status', 'LOCKED'),
        ('MCP_ACCOUNT_STATUS', {'p_username': 'DB_HEALTH_AGENT'}, 'account_status', 'OPEN'),
        ('MCP_ACCOUNT_STATUS', {'p_username': 'PAF_MCP_MISSING'}, 'status', 'not_found'),
        ('MCP_ACCOUNT_STATUS', {'p_username': 'ADMIN'}, 'status', 'invalid_input'),
        ('MCP_ACCOUNT_STATUS', {'p_username': "PAF_MCP_DEMO' OR '1'='1"}, 'status', 'invalid_input'),
        ('MCP_LOGIN_PRIVILEGES', {'p_username': 'PAF_MCP_DEMO'}, 'direct_create_session', 1),
        ('MCP_LOGIN_PRIVILEGES', {'p_username': 'ADMIN'}, 'status', 'invalid_input'),
    ]
    for name, arguments, key, wanted in cases:
        result = call('tools/call', {'name': name, 'arguments': arguments})
        if result.get('isError'):
            raise RuntimeError(f'{name} reported a tool error; output withheld.')
        text = '\n'.join(block['text'] for block in result.get('content', []) if block.get('type') == 'text')
        data = json.loads(text)
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict) or data.get(key) != wanted:
            raise RuntimeError(f'{name}: unexpected {key}; output withheld.')
        print(f'PASS: {name} / {key}={wanted}')
    print('Direct MCP tool tests passed. PAF end-to-end compatibility is a separate check.')
    return 0 if notification_ok else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (urllib.error.URLError, RuntimeError, ValueError, KeyError) as error:
        # Never emit HTTP response bodies, tokens, passwords or query outputs.
        print(f'CHECK FAILED: {type(error).__name__}: {error}')
        raise SystemExit(1)
