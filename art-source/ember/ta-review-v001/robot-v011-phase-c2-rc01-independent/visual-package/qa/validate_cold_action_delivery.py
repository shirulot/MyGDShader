"""检查实际GPU冷加载回执及冻结/ZIP/冷副本载荷；输出仅写包外。"""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
delivery = json.loads((root / 'qa/delivery_phase-c1-rc01.json').read_text(encoding='utf-8'))
cold = Path(delivery['cold_root'])
frozen = root / 'review/phase-c1-rc01'
output = root / 'qa/cold-action-validation/c1-rc01'
digest = lambda data: hashlib.sha256(data).hexdigest()
catalog = json.loads((frozen / 'sha256-manifest.json').read_text(encoding='utf-8'))
gpu = json.loads((output / 'qa/godot_action_pilot_v011.json').read_text(encoding='utf-8'))
metadata = json.loads((frozen / 'action-pilot-metadata.json').read_text(encoding='utf-8'))
errors = []
for prefix, folder in [('frozen', frozen), ('cold', cold)]:
    for item in catalog['files']:
        if digest((folder / item['file']).read_bytes()) != item['sha256']:
            errors.append(prefix + ' payload changed: ' + item['file'])
archive = Path(delivery['zip'])
if digest(archive.read_bytes()) != delivery['zip_sha256']:
    errors.append('ZIP changed')
with zipfile.ZipFile(archive) as pack:
    for item in catalog['files']:
        if digest(pack.read(item['file'])) != item['sha256']:
            errors.append('ZIP payload changed: ' + item['file'])
if gpu['technical_checks'] != 'PASS' or gpu['atlas_sha256'] != metadata['atlas_sha256']:
    errors.append('GPU report failed or stale')
if len(gpu['cases']) != 30 or not all(case['rgba_exact'] for case in gpu['cases']):
    errors.append('Incomplete GPU samples')
if not gpu['collect_to_idle']['idle0_rgba_exact'] or gpu['collect_to_idle']['collect_sequence'] != [0, 1, 2, 3]:
    errors.append('Invalid collect recovery')
for log in ['import-error.log', 'gpu-error.log']:
    if (output / log).read_text(encoding='utf-8').strip():
        errors.append('Nonempty error log: ' + log)
report = dict(delivery, status='FAIL' if errors else 'PASS', atlas_sha256=metadata['atlas_sha256'],
              actual_gpu_cases=len(gpu['cases']), natural_playback=gpu['natural_playback'],
              collect_to_idle=gpu['collect_to_idle'], errors=errors,
              cold_payload_changes_after_engine=len([item for item in errors if item.startswith('cold payload')]),
              engine_outputs='qa/cold-action-validation/c1-rc01',
              frozen_and_zip_read_only=True, art_acceptance='PENDING_TA')
report['cold_engine_validation'] = report['status']
(root / 'qa/cold_delivery_validation_c1_rc01.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'payloads': len(catalog['files']), 'gpu': len(gpu['cases']), 'errors': errors}))
if errors:
    raise SystemExit(1)
