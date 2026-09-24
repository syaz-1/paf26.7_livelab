#!/usr/bin/env python3
"""Retest saved prompts against the Select AI flow; API key supplied via stdin."""
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
import ssl
import sys
import time
from paf_client import Client, ROOT, KNOWN_CERT_SHA256

AGENT = '5C23F409991ADC49E0634815000AD1E6'

def save(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as f:
        json.dump(value, f, indent=2)

def main():
    key = sys.stdin.readline().strip()
    if not key.startswith('afk_'):
        raise ValueError('API key must be supplied through stdin')
    client = Client()
    client.login()
    status, flow = client.request('GET', '/agentFactory/v1/agents/' + AGENT)
    assert status == 200
    nodes = flow['data']['data']['nodes']
    assert {n['data']['type'] for n in nodes} == {'selectAIProfile', 'chatInputComponent', 'chatOutputComponent'}
    selects = [n['data']['template'] for n in nodes if n['data']['type'] == 'selectAIProfile']
    assert len(selects) == 1
    t = selects[0]
    assert t['action']['value'] == 'runsql'
    assert t['profile_name_action']['value'] == 'DB_HEALTH_AGENT'
    assert t['database_action']['value'] == '5C29A4176B58116DE0634815000A1FDA'
    status, memory = client.request('GET', '/agentFactory/v1/agentBuilder/memory/settings/' + AGENT)
    cases = json.loads((ROOT / 'tests/paf/prompts.json').read_text())['cases']
    folder = ROOT / '.local/paf-tests' / ('select-ai-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir(mode=0o700)
    save(folder / 'metadata.json', {'agent_id':AGENT, 'profile':'DB_HEALTH_AGENT', 'action':'runsql', 'memory':memory.get('data') if status == 200 else None, 'case_count':len(cases), 'grading_note':'Evaluate original behaviors; GET_* routine names are not applicable to this Select AI flow.'})
    print('RESULT_DIRECTORY:', folder.relative_to(ROOT), flush=True)
    results, rooms = [], set()
    for case in cases:
        start = time.monotonic()
        entry = {**case, 'started_at_utc':datetime.now(timezone.utc).isoformat(), 'behavioral_verdict':'NOT_REVIEWED'}
        conn = http.client.HTTPSConnection(client.host, client.port, context=ssl._create_unverified_context(), timeout=180)
        try:
            conn.connect()
            if hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest() != KNOWN_CERT_SHA256:
                raise RuntimeError('Certificate changed')
            conn.request('POST', '/agentFactory/v1/integrations/agents/' + AGENT + '/run', body=json.dumps({'message':case['prompt']}), headers={'Authorization':'Bearer ' + key, 'Content-Type':'application/json'})
            response = conn.getresponse()
            raw = client.redact(response.read().decode()).replace(key, '[REDACTED]')
            body = json.loads(raw)
            room = body.get('roomId')
            entry.update(http_status=response.status, response=body, unique_room=bool(room and room not in rooms))
            if room: rooms.add(room)
        except Exception as exc:
            entry.update(http_status=None, error=type(exc).__name__)
        finally:
            conn.close()
        entry['duration_seconds'] = round(time.monotonic()-start,2)
        results.append(entry)
        save(folder / (case['id']+'.json'), entry)
        save(folder / 'results.json', results)
        message = entry.get('response',{}).get('message','')
        print(case['id'], 'HTTP',entry['http_status'], 'database_error', 'Database error:' in message or 'ORA-' in message, 'seconds',entry['duration_seconds'],flush=True)
        if entry['http_status'] in (401,403): break
    print('COMPLETE',len(results),flush=True)

if __name__ == '__main__':
    main()
