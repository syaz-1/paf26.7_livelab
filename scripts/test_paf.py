#!/usr/bin/env python3
"""Run the 21 saved prompts through a published Agent Factory flow.

Results are private local artifacts. HTTP success is not a behavioral pass;
answer quality and tool evidence must be reviewed separately.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import quote
from paf_client import Client, ROOT


def save(path, text):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent-id', required=True)
    parser.add_argument('--resume', type=Path, help='Existing private result directory')
    args = parser.parse_args()
    cases = json.loads((ROOT / 'tests/paf/prompts.json').read_text())['cases']
    client = Client()
    client.login()
    status, flow = client.request('GET', '/agentFactory/v1/agents/' + quote(args.agent_id, safe=''))
    if status != 200:
        raise RuntimeError('Could not inspect target flow.')
    data = flow['data']
    nodes = data['data']['nodes']
    allowed_types = {'agentStep', 'oraclePLSQLExecutor', 'chatInputComponent', 'chatOutputComponent'}
    if any(n['data']['type'] not in allowed_types for n in nodes):
        raise RuntimeError('Flow contains unreviewed node types; review before testing.')
    expected = {'GET_DATABASE_OVERVIEW', 'GET_FAILED_JOBS', 'GET_SESSIONS', 'GET_SQL_WORKLOAD', 'GET_STORAGE_USAGE'}
    executors = [n['data'] for n in nodes if n['data']['type'] == 'oraclePLSQLExecutor']
    if len(executors) != 1:
        raise RuntimeError('Expected exactly one reviewed database executor.')
    template = executors[0]['template']
    selected = {json.loads(v)['qualified_name'] for v in template['allowed_routines']['value']}
    if selected != {'DB_HEALTH_AGENT.DB_HEALTH_API.' + n for n in expected}:
        raise RuntimeError('Flow tool selection differs from the five approved read-only routines.')
    if template['auto_commit']['value']:
        raise RuntimeError('Unexpected auto-commit setting.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = args.resume.resolve() if args.resume else ROOT / '.local/paf-tests' / stamp
    if not folder.resolve().is_relative_to((ROOT / '.local/paf-tests').resolve()):
        raise ValueError('Results must remain in the private test directory.')
    folder.mkdir(parents=True, mode=0o700, exist_ok=bool(args.resume))
    folder.chmod(0o700)
    memory_status, memory_response = client.request('GET', '/agentFactory/v1/agentBuilder/memory/settings/' + quote(args.agent_id, safe=''))
    memory_settings = memory_response.get('data') if memory_status == 200 and isinstance(memory_response, dict) else None
    metadata = {'started_at_utc': stamp, 'agent_id':args.agent_id, 'flow_name':data['name'],
                'updated_at':data.get('updatedAt'), 'case_count':len(cases),
                'method':'POST published run API; no roomId supplied; distinct rooms, but shared agent memory may influence answers',
                'tool_evidence':'Final-answer API does not itself include tool traces.',
                'selected_routines':sorted(selected), 'memory_settings':memory_settings}
    if not args.resume:
        save(folder / 'metadata.json', client.redact(metadata))
    print('RESULT_DIRECTORY:', folder.relative_to(ROOT), flush=True)
    results = json.loads((folder / 'results.json').read_text()) if args.resume else []
    completed = {r['id'] for r in results}
    rooms = {r.get('response', {}).get('roomId') for r in results if isinstance(r.get('response'), dict)}
    for case in cases:
        if case['id'] in completed:
            continue
        started = datetime.now(timezone.utc).isoformat()
        clock = time.monotonic()
        result = {**case, 'started_at_utc':started, 'behavioral_verdict':'NOT_REVIEWED'}
        try:
            status, response = client.request('POST', '/agentFactory/v1/agentBuilder/run/' + quote(args.agent_id, safe=''),
                {'message':case['prompt']}, timeout=180)
            result.update(http_status=status, response=response)
            room = response.get('roomId') if isinstance(response, dict) else None
            result['unique_room'] = bool(room and room not in rooms)
            if room:
                rooms.add(room)
            message = response.get('message') if isinstance(response,dict) else None
            result['transport_ok'] = status == 200 and bool(message)
        except Exception as exc:
            result.update(http_status=None, transport_ok=False, error=type(exc).__name__)
        result['duration_seconds'] = round(time.monotonic()-clock,2)
        save(folder / (case['id']+'.json'), client.redact(result))
        results.append(result)
        save(folder / 'results.json', client.redact(results))
        print(case['id'], 'HTTP',result.get('http_status'), 'seconds',result['duration_seconds'],
              'unique_room',result.get('unique_room'),flush=True)
    print('COMPLETE:',len(results),'cases;',sum(bool(r['transport_ok']) for r in results),'responses received',flush=True)


if __name__ == '__main__':
    main()
