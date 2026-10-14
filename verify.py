"""Synthetic queue experiment. Contains no Dopamina application code."""
import json
import os
import pathlib
import subprocess
import time
from app import total

root = pathlib.Path(__file__).resolve().parent
event = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text()) if os.getenv('GITHUB_EVENT_PATH') else {}
event_name = os.getenv('GITHUB_EVENT_NAME', 'local')
base = (event.get('merge_group', {}).get('base_sha') if event_name == 'merge_group'
        else event.get('pull_request', {}).get('base', {}).get('sha'))
revisions = [json.loads(p.read_text()) for p in sorted((root / 'migrations').glob('*.json'))]
by_id = {r['id']: r for r in revisions}
assert len(by_id) == len(revisions), 'Duplicate migration revision'
parents = {r['parent'] for r in revisions if r['parent'] is not None}
assert parents <= by_id.keys(), 'Missing migration parent'
heads = by_id.keys() - parents
assert len(heads) == 1, f'Expected exactly one migration head, got {sorted(heads)}'
chain = []
cursor = next(iter(heads))
while cursor is not None:
    assert cursor not in chain, 'Migration cycle'
    chain.append(cursor)
    cursor = by_id[cursor]['parent']
assert len(chain) == len(revisions), 'Disconnected migration'
chain.reverse()
assert total([2, 3]) == 5
assert total([]) == 0

if os.getenv('VERIFY_POSTGRES') == 'true':
    # The service is dedicated to this job and contains only synthetic tables.
    def sql(statement):
        subprocess.run(['docker', 'exec', os.environ['POSTGRES_CONTAINER'], 'psql',
                        '-U', 'sandbox', '-d', 'sandbox', '-v', 'ON_ERROR_STOP=1',
                        '-c', statement], check=True, stdout=subprocess.DEVNULL)
    for revision in chain:
        sql(by_id[revision]['up'])
    for revision in reversed(chain):
        sql(by_id[revision]['down'])
    for revision in chain:
        sql(by_id[revision]['up'])

delay = int((root / 'queue-delay.txt').read_text()) if (root / 'queue-delay.txt').exists() else 0
if event_name == 'merge_group':
    assert 0 <= delay <= 90
    time.sleep(delay)
receipt = {'event': event_name, 'base_sha': base, 'head_sha': os.getenv('GITHUB_SHA'),
           'runner': os.getenv('RUNNER_NAME'), 'migration_head': next(iter(heads)),
           'migration_count': len(revisions), 'postgres_round_trip': os.getenv('VERIFY_POSTGRES') == 'true'}
(root / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
