#!/usr/bin/env python3
"""Run the Appendix D suite in fresh PAF rooms; retain live evidence privately."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from paf_client import Client, ROOT


def save(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        json.dump(value, stream, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent-id', required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2, 3), default=1,
                        help='Default 1 matches a participant testing sequentially')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-F0-9]{32}', args.agent_id):
        parser.error('Expected a PAF agent ID')
    client = Client(); client.login()
    path = '/agentFactory/v1/agents/' + args.agent_id
    status, response = client.request('GET', path)
    assert status == 200
    graph = response['data']['data']
    templates = {n['data']['type']: n['data']['template'] for n in graph['nodes']}
    assert set(templates['mcpServer']['allowedTools']['value']) == {'MCP_ACCOUNT_STATUS', 'MCP_LOGIN_PRIVILEGES'}
    instructions = templates['agentStep']['custom_instruction']['value']
    assert instructions == (ROOT / 'docs/livelab-mcp/files/agent-instructions.txt').read_text()
    status, memory = client.request('GET', '/agentFactory/v1/agentBuilder/memory/settings/' + args.agent_id)
    assert status == 200 and memory['data']['enabled'] is False
    cases = []
    for line in (ROOT / 'docs/livelab-paf-only/files/mcp-test-prompts.md').read_text().splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 3 and re.fullmatch(r'(normal|nontechnical|gibberish|timezone|safety)-\d{2}', cells[0]):
            cases.append(dict(id=cells[0], prompt=cells[1], expected=cells[2]))
    assert len(cases) == 15 and len({c['id'] for c in cases}) == 15
    folder = ROOT / '.local/paf-tests' / ('mcp-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700, parents=True)
    save(folder / 'metadata.json', dict(agent_id=args.agent_id, graph=graph, memory=memory['data'],
         instruction_sha256=hashlib.sha256(instructions.encode()).hexdigest(),
         note='HTTP success is not a behavioral pass. Review answers and traces separately.'))
    print('RESULT_DIRECTORY', folder, flush=True)

    def run(case):
        c = Client()
        entry = dict(case, started_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            c.login()
            status, result = c.request('POST', '/agentFactory/v1/agentBuilder/run/' + args.agent_id,
                                       {'message': case['prompt']}, timeout=180)
            entry.update(http_status=status, response=json.loads(c.redact(result)))
        except Exception as exc:
            entry.update(http_status=None, error=type(exc).__name__)
        save(folder / (case['id'] + '.json'), entry)
        return entry

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run, c) for c in cases]):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    save(folder / 'results.json', sorted(results, key=lambda r: r['id']))
    status, current = client.request('GET', path)
    assert status == 200 and current['data']['data'] == graph, 'Workflow changed during validation'
    print('COMPLETE: 15 cases; configuration unchanged during run.', flush=True)


if __name__ == '__main__':
    main()
