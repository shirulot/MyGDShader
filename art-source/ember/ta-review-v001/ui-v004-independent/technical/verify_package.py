"""TA 只读固定包核验与安全冷解包；仅修改冷副本的用户存储隔离配置。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/ui-v004-independent/technical'
cold = review / 'cold-project'
zip_path = workspace / 'art-source/ember/deliveries/ui_edge_interactions_v004_2026-10-06.zip'
checks = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check(name, passed, **details):
    checks.append(dict(name=name, passed=bool(passed), **details))

def read_json(data):
    return json.loads(data.decode('utf-8-sig'))

check('fixed_zip_sha', sha(zip_path.read_bytes()) == 'cb61690d89244a2f8dc71d1905a0102399aa6ce063ff1c439d18a9727df8c194')
check('fixed_zip_bytes', zip_path.stat().st_size == 16705277)
with ZipFile(zip_path) as package:
    manifest = read_json(package.read('package-manifest.json'))
    check('manifest_file_count', len(manifest['files']) == 226)
    all_files = [item.filename for item in package.infolist() if not item.is_dir()]
    check('manifest_zip_set', len(all_files) == len(set(all_files)) and set(all_files) == {entry['path'] for entry in manifest['files']} | {'package-manifest.json'})
    for entry in manifest['files']:
        data = package.read(entry['path'])
        check('manifest:' + entry['path'], len(data) == entry['bytes'] and sha(data) == entry['sha256'])
    inputs = read_json(package.read('input-manifest.json'))
    for entry in inputs['inputs']:
        if Path(entry['path']).suffix in ['.gd', '.tscn', '.tres', '.png']:
            source = workspace / entry['path']
            check('workspace_source:' + entry['path'], source.exists() and sha(source.read_bytes()) == entry['sha256'] and sha(package.read(entry['path'])) == entry['sha256'])
    summary = read_json(package.read('art-source/ember/ui-interactions-v004/validation-summary.json'))
    for path, expected in summary['protected_source_hashes'].items():
        check('protected:' + path, sha((workspace / path).read_bytes()).lower() == expected.lower())
    for path, expected in summary['source_sha256'].items():
        relative = path.removeprefix('res://')
        check('summary_source:' + relative, sha(package.read(relative)) == expected and sha((workspace / relative).read_bytes()) == expected)
    for filename in all_files:
        target = (cold / filename).resolve()
        assert target.is_relative_to(cold.resolve()), 'Unsafe archive path'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(filename))

project = cold / 'project.godot'
project_original_sha = sha(project.read_bytes())
text = project.read_text(encoding='utf-8-sig')
text = text.replace('[application]', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA UI v004 Independent"')
project.write_text(text, encoding='utf-8')
failures = [entry for entry in checks if not entry['passed']]
report = {'status': 'PASS' if not failures else 'FAIL', 'check_count': len(checks), 'failures': failures, 'checks': checks, 'zip_sha256': sha(zip_path.read_bytes()), 'protected_count': 5, 'cold_project': str(cold), 'cold_config_isolation': {'original_sha256': project_original_sha, 'review_sha256': sha(project.read_bytes()), 'only_change': 'custom user directory isolation'}}
(review / 'package-integrity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key not in ['checks']}, ensure_ascii=False))
