"""验证 C2 新解压副本的实际 GPU 回执，输出只写包外，原载荷逐项再核哈希。"""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
delivery = json.loads((root / 'qa/delivery_phase-c2-rc01.json').read_text(encoding='utf-8'))
cold = Path(delivery['cold_root'])
frozen = root / 'review/phase-c2-rc01'
output = root / 'qa/cold-full-validation/c2-rc01'
digest = lambda data: hashlib.sha256(data).hexdigest()
catalog = json.loads((frozen / 'sha256-manifest.json').read_text(encoding='utf-8'))
gpu = json.loads((output / 'qa/godot_full_actions_v011.json').read_text(encoding='utf-8'))
metadata = json.loads((frozen / 'full-action-metadata.json').read_text(encoding='utf-8'))
errors = []
for prefix, folder in [('frozen', frozen), ('cold', cold)]:
    if digest((folder / 'sha256-manifest.json').read_bytes()) != delivery['sha256_manifest_sha256']:
        errors.append(prefix + ' manifest changed')
    for item in catalog['files']:
        if digest((folder / item['file']).read_bytes()) != item['sha256']:
            errors.append(prefix + ' payload changed: ' + item['file'])
archive = Path(delivery['zip'])
if digest(archive.read_bytes()) != delivery['zip_sha256']:
    errors.append('ZIP changed')
with zipfile.ZipFile(archive) as pack:
    if digest(pack.read('sha256-manifest.json')) != delivery['sha256_manifest_sha256']:
        errors.append('ZIP manifest changed')
    for item in catalog['files']:
        if digest(pack.read(item['file'])) != item['sha256']:
            errors.append('ZIP payload changed: ' + item['file'])
if gpu['technical_checks'] != 'PASS' or gpu['errors'] or gpu['atlas_sha256'] != metadata['atlas_sha256']:
    errors.append('GPU report failed or stale')
if len(gpu['cases']) != 224 or not all(case['rgba_exact'] for case in gpu['cases']):
    errors.append('Incomplete GPU samples')
if len(gpu['transitions']) != 136 or not all(case['rgba_exact'] and case['root_unchanged'] for case in gpu['transitions']):
    errors.append('Invalid transitions')
if len(gpu['natural_playback']) != 16:
    errors.append('Incomplete natural playback')
if len(gpu['collect_to_idle']) != 8:
    errors.append('Incomplete collection recovery')
for case in gpu['collect_to_idle']:
    if not case['idle0_rgba_exact'] or case['sequence'] != [0, 1, 2, 3] or len(case['finished_events']) != 1 or case['result_frame'] != 0:
        errors.append('Invalid collect recovery: ' + case['direction'])
for log in ['import-error.log', 'gpu-error.log']:
    if (output / log).read_text(encoding='utf-8').strip():
        errors.append('Nonempty error log: ' + log)
report = dict(delivery, status='FAIL' if errors else 'PASS', atlas_sha256=metadata['atlas_sha256'],
              actual_gpu_cases=len(gpu['cases']), actual_transitions=len(gpu['transitions']),
              natural_playback=gpu['natural_playback'], collect_to_idle=gpu['collect_to_idle'], errors=errors,
              cold_payload_changes_after_engine=len([item for item in errors if item.startswith('cold payload')]),
              engine_outputs='qa/cold-full-validation/c2-rc01', frozen_and_zip_read_only=True, art_acceptance='PENDING_TA')
report['cold_engine_validation'] = report['status']
(root / 'qa/cold_delivery_validation_c2_rc01.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'payloads': len(catalog['files']), 'gpu': len(gpu['cases']), 'transitions': len(gpu['transitions']), 'recoveries': len(gpu['collect_to_idle']), 'errors': errors}))
if errors:
    raise SystemExit(1)
