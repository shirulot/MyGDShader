"""建筑迁移只读核验：路径映射、before SHA 和原冻结 ZIP，不启动 Godot。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
PKG = ROOT/'assets/ember/buildings_final'
PLAN = PKG/'review/relocation-plan.json'
REPAIR = PKG/'verification/path-repair.json'
RESULT = PKG/'verification/relocation-result.json'

def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))

plan, repairs, result = load(PLAN), load(REPAIR), load(RESULT)
assert Path(plan['workspace']).resolve() == ROOT.resolve()
assert plan['package'] == 'assets/ember/buildings_final'
rows = plan['files']
assert len(rows) == 308
assert len({r['from'].casefold() for r in rows}) == len(rows)
assert len({r['to'].casefold() for r in rows}) == len(rows)
operations = plan['operations']
opcounts = Counter()
evidence, failures = [], []
repair_by_path = {r['path']:r for r in repairs}
for row in rows:
    for field in ['from','to']:
        rel = PurePosixPath(row[field])
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in row[field]
        assert (ROOT/row[field]).resolve().is_relative_to(ROOT.resolve())
    target = ROOT/row['to']
    assert target.resolve().is_relative_to(PKG.resolve())
    matches = [(i,op) for i,op in enumerate(operations)
        if row['from'] == op['from'] or (op['kind']=='directory' and row['from'].startswith(op['from']+'/'))]
    assert len(matches) == 1, (row['from'],matches)
    i,op = matches[0]
    assert row['to'] == op['to']+row['from'][len(op['from']):]
    opcounts[i] += 1
    record = dict(row)
    record['old_path_present_now'] = (ROOT/row['from']).exists()
    record['target_present_now'] = target.is_file()
    if record['old_path_present_now']: failures.append({'kind':'old_path_still_present','path':row['from']})
    if not record['target_present_now']:
        failures.append({'kind':'missing_target','path':row['to']})
        evidence.append(record)
        continue
    data = target.read_bytes()
    record['current_sha256'] = sha(data)
    record['current_bytes'] = len(data)
    record['before_sha_preserved'] = record['current_sha256'] == row['sha256']
    if not record['before_sha_preserved']:
        repair = repair_by_path.get(row['to'])
        record['path_repair_record'] = repair
        record['matches_recorded_after_sha'] = bool(repair and repair['after_sha256'] == record['current_sha256'])
    evidence.append(record)
assert all(opcounts[i] == op['files'] for i,op in enumerate(operations))
assert sum(r['bytes'] for r in rows) == 93339422 == result['moved_file_bytes']
assert result['moved_files'] == len(rows)
assert not failures, failures

# 独立展开关键保护集合：包含所有 PNG、Shader、ZIP 与历史审查文件，去重。
# 不把制作方未给成员列表的115计数直接冒称独立检查集合。
critical = [r for r in evidence if Path(r['to']).suffix.lower() in {'.png','.gdshader','.zip'}
    or r['to'].startswith('assets/ember/buildings_final/review/')]
assert len(critical) == 149
assert all(r['before_sha_preserved'] and r['current_bytes']==r['bytes'] for r in critical)
mainproject = ROOT/'project.godot'
assert sha(mainproject.read_bytes()) == plan['main_project_sha256']

frozen = PKG/'delivery/building_assets_v004r1_2026-10-06.zip'
zip_sha = sha(frozen.read_bytes())
assert zip_sha == '22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32'
zipbindings = []
with ZipFile(frozen) as z:
    assert z.testzip() is None and len(z.namelist()) == 79
    manifest = json.loads(z.read('DELIVERY_MANIFEST.json').decode('utf-8-sig'))['files']
    assert len(manifest) == 78
    for entry in manifest:
        data = z.read(entry['path'])
        assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
    def map_catalog_strings(value):
        if isinstance(value,dict): return {k:map_catalog_strings(v) for k,v in value.items()}
        if isinstance(value,list): return [map_catalog_strings(v) for v in value]
        if isinstance(value,str):
            for old,new in sorted(plan['mapping'].items(),key=lambda item:-len(item[0])):
                value=value.replace(old,new)
        return value
    original_catalog=json.loads(z.read('assets/ember/building_assets_v004r1/catalog_v004r1.json').decode('utf-8-sig'))
    mapped_catalog=map_catalog_strings(original_catalog)
    assert mapped_catalog == load(PKG/'textures/catalog_v004r1.json')
    assert mapped_catalog == load(PKG/'examples/standalone/assets/ember/buildings_final/textures/catalog_v004r1.json')
    # 正式32PNG+独立例程的32副本；母稿与用户选图；原Shader的两个工作副本。
    for name in z.namelist():
        target = None
        if name.startswith('assets/ember/building_assets_v004r1/') and name.endswith('.png'):
            target = PKG/'textures'/name.removeprefix('assets/ember/building_assets_v004r1/')
            copy = PKG/'examples/standalone/assets/ember/buildings_final/textures'/name.removeprefix('assets/ember/building_assets_v004r1/')
            assert copy.read_bytes() == z.read(name)
        elif name.startswith('art-source/ember/building-assets-v004/masters/') or name.startswith('art-source/ember/selected-buildings-v001/references/'):
            target = PKG/'source'/name.removeprefix('art-source/ember/')
        elif name == 'shaders/ember/building_intact_v004.gdshader':
            target = PKG/'shaders/building_intact.gdshader'
            assert (PKG/'examples/standalone/assets/ember/buildings_final/shaders/building_intact.gdshader').read_bytes() == z.read(name)
        if target is not None:
            assert target.read_bytes() == z.read(name)
            zipbindings.append({'zip_member':name,'current_path':target.relative_to(ROOT).as_posix(),
                'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'byte_identical':True})
assert len(zipbindings) == 39

changed = [r for r in evidence if not r['before_sha_preserved']]
unrecorded = [r['to'] for r in changed if not r['path_repair_record']]
stale_after = [r['to'] for r in changed if r['path_repair_record'] and not r['matches_recorded_after_sha']]
report = {'status':'RELOCATION_MAPPING_AND_ART_HISTORY_INTEGRITY_PASS',
    'checked_at_utc':datetime.now(timezone.utc).isoformat(),
    'plan_sha256':sha(PLAN.read_bytes()),'relocation_result_sha256':sha(RESULT.read_bytes()),
    'path_repair_sha256':sha(REPAIR.read_bytes()),'moved_files_checked':len(evidence),
    'operations_checked':len(operations),'mapping_root_entries':len(plan['mapping']),
    'missing_targets':[],'old_paths_present_now':[],'unsafe_mapping_paths':[],
    'plan_before_bytes':sum(r['bytes'] for r in rows),
    'current_before_sha_preserved_files':sum(r['before_sha_preserved'] for r in evidence),
    'critical_unique_files_independently_rehashed':len(critical),
    'critical_categories':{'all_png_files':83,'shader_files':2,'frozen_zip':1,'historical_review_files':65,'overlap_png_in_history':2},
    'producer_protected_count':result['protected_files_unchanged'],
    'producer_protected_count_limit':'The receipt gives115 but no explicit member list; independent scope is the enumerated149-file union and all308-file census.',
    'main_project_sha256':plan['main_project_sha256'],
    'original_ta_receipt_sha256':sha((PKG/'review/ta-review.md').read_bytes()),
    'frozen_zip_sha256':zip_sha,'frozen_zip_entries':79,'frozen_manifest_payloads':78,
    'current_catalog_and_standalone_catalog_equal_original_zip_after_declared_path_mapping':True,
    'zip_to_current_bindings':zipbindings,'file_records':evidence,
    'current_changed_extensions':dict(Counter(Path(r['to']).suffix for r in changed)),
    'changed_not_in_path_repair':unrecorded,'recorded_after_sha_no_longer_current':stale_after,
    'scope_limit':'No image acceptance review or Godot run. Intentional path text, regenerated import/UID and runtime validation evidence are separate from art/history byte preservation. Code semantics delegated to the other auditor.'}
(OUT/'binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','checked_at_utc','plan_sha256','relocation_result_sha256',
    'moved_files_checked','operations_checked','critical_unique_files_independently_rehashed','current_before_sha_preserved_files',
    'current_changed_extensions','changed_not_in_path_repair']},ensure_ascii=False,indent=2))
print('recorded_after_sha_stale',len(stale_after))
