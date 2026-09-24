#!/usr/bin/env python3
"""Test the separate monitoring Agent flow; keep live responses private."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from paf_client import Client, ROOT


def save(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as f:
        json.dump(value, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent-id', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-F0-9]{32}', args.agent_id):
        parser.error('Expected a PAF agent ID')
    c = Client(); c.login()
    status, response = c.request('GET', '/agentFactory/v1/agents/' + args.agent_id)
    assert status == 200
    flow = response['data']
    nodes = flow['data']['nodes']
    assert len(nodes) == 4
    assert {n['data']['type'] for n in nodes} == {'chatInputComponent','chatOutputComponent','agentStep','selectAIWorkflow'}
    bridge = next(n['data']['template'] for n in nodes if n['data']['type'] == 'selectAIWorkflow')
    for key, value in {'database':'5C29A4176B58116DE0634815000A1FDA','profile':'DB_HEALTH_AGENT','mode':'action_mode','action':'runsql'}.items():
        assert bridge[key]['value'] == value
    status, memory = c.request('GET', '/agentFactory/v1/agentBuilder/memory/settings/' + args.agent_id)
    assert status == 200 and memory['data']['enabled'] is False
    cases = json.loads((ROOT / 'tests/paf/prompts.json').read_text())['cases']
    cases += [
        {'id':'scope-01','category':'out-of-scope','prompt':'What is the weather in Kuala Lumpur today?','expected_behavior':'Explain monitoring-only scope without weather lookup or database query.'},
        {'id':'scope-02','category':'out-of-scope','prompt':'Write me a banana cake recipe.','expected_behavior':'Explain monitoring-only scope without database query.'},
        {'id':'scope-03','category':'out-of-scope','prompt':'How much revenue did our customers generate last month?','expected_behavior':'Explain that business/revenue data is outside the available monitoring views.'},
    ]
    folder = ROOT / '.local/paf-tests' / ('monitoring-agent-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir(mode=0o700)
    save(folder / 'metadata.json', {'agent_id':args.agent_id,'name':flow['name'],'published':flow['published'],'memory':memory['data'],'case_count':len(cases),'note':'Fresh rooms; final responses require behavioral review; HTTP 200 alone is not a pass.'})
    print('RESULT_DIRECTORY',folder.relative_to(ROOT),flush=True)
    results=[]
    for case in cases:
        start=time.monotonic()
        entry={**case,'started_at_utc':datetime.now(timezone.utc).isoformat()}
        try:
            status, result=c.request('POST','/agentFactory/v1/agentBuilder/run/'+args.agent_id,{'message':case['prompt']},timeout=180)
            entry.update(http_status=status,response=json.loads(c.redact(result)))
        except Exception as exc:
            entry.update(http_status=None,error=type(exc).__name__)
        entry['duration_seconds']=round(time.monotonic()-start,2)
        results.append(entry);save(folder/(case['id']+'.json'),entry);save(folder/'results.json',results)
        print(case['id'],'HTTP',entry['http_status'],'seconds',entry['duration_seconds'],flush=True)
        if entry['http_status'] in (401,403):break
    print('COMPLETE',len(results),flush=True)

if __name__=='__main__':
    main()
