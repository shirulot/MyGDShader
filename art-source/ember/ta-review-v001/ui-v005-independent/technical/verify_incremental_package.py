"""冻结 v005 冷解包、来源/保护验证，并与已独立核验 v004 固定 ZIP 做精确增量。"""
import difflib
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/ui-v005-independent/technical'
cold = review / 'cold-project'
zip_path = workspace / 'art-source/ember/deliveries/ui_edge_interactions_v005_2026-10-06.zip'
old_zip_path = workspace / 'art-source/ember/deliveries/ui_edge_interactions_v004_2026-10-06.zip'
checks = []

def sha(data): return hashlib.sha256(data).hexdigest()
def read(data): return json.loads(data.decode('utf-8-sig'))
def check(name, passed, **details): checks.append(dict(name=name, passed=bool(passed), **details))

check('fixed_zip_sha', sha(zip_path.read_bytes()) == '7792955f87603d5efbfda61dcf999b9b761370552463dc69d8cc8167f7d31a7e')
check('fixed_zip_bytes', zip_path.stat().st_size == 16709201)
with ZipFile(zip_path) as package, ZipFile(old_zip_path) as old_package:
    manifest = read(package.read('package-manifest.json'))
    check('manifest_count_231', len(manifest['files']) == 231)
    names = [item.filename for item in package.infolist() if not item.is_dir()]
    old_names = {item.filename for item in old_package.infolist() if not item.is_dir()}
    check('manifest_exact_entry_set', len(names) == len(set(names)) and set(names) == {entry['path'] for entry in manifest['files']} | {'package-manifest.json'})
    for entry in manifest['files']:
        data = package.read(entry['path'])
        check('manifest:' + entry['path'], len(data) == entry['bytes'] and sha(data) == entry['sha256'])
    inputs = read(package.read('input-manifest.json'))
    for entry in inputs['inputs']:
        if Path(entry['path']).suffix in ['.gd', '.tscn', '.tres', '.png']:
            source = workspace / entry['path']
            check('workspace_source:' + entry['path'], source.exists() and sha(source.read_bytes()) == entry['sha256'] and sha(package.read(entry['path'])) == entry['sha256'])
    summary = read(package.read('art-source/ember/ui-interactions-v004/validation-summary.json'))
    for path, expected in summary['protected_source_hashes'].items(): check('protected:' + path, sha((workspace / path).read_bytes()).lower() == expected.lower())
    for path, expected in summary['source_sha256'].items():
        relative = path.removeprefix('res://')
        check('summary_source:' + relative, sha(package.read(relative)) == expected and sha((workspace / relative).read_bytes()) == expected)
    common = set(names) & old_names
    changed = sorted(name for name in common if package.read(name) != old_package.read(name))
    added = sorted(set(names) - old_names)
    removed = sorted(old_names - set(names))
    changed_scripts = [name for name in changed if name.endswith('.gd')]
    check('only_existing_script_change_interaction_ui', changed_scripts == ['scripts/ember/ui_edge_v004/interaction_ui.gd'], changed=changed_scripts)
    check('no_removed_files', not removed)
    pngs = [name for name in common if name.endswith('.png')]
    check('existing_pngs_byte_identical', all(package.read(name) == old_package.read(name) for name in pngs), count=len(pngs))
    original_ui = old_package.read(changed_scripts[0]).decode('utf-8-sig').splitlines(keepends=True)
    new_ui = package.read(changed_scripts[0]).decode('utf-8-sig').splitlines(keepends=True)
    review.mkdir(parents=True, exist_ok=True)
    (review / 'interaction-ui-v004-to-v005.diff').write_text(''.join(difflib.unified_diff(original_ui, new_ui, fromfile='fixed-v004/interaction_ui.gd', tofile='fixed-v005/interaction_ui.gd')), encoding='utf-8')
    for filename in names:
        target = (cold / filename).resolve()
        assert target.is_relative_to(cold.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(filename))

project = cold / 'project.godot'
original_config_sha = sha(project.read_bytes())
text = project.read_text(encoding='utf-8-sig').replace('[application]', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA UI v005 Independent"')
project.write_text(text, encoding='utf-8')
failures = [entry for entry in checks if not entry['passed']]
report = {'status':'PASS' if not failures else 'FAIL','check_count':len(checks),'failures':failures,'checks':checks,'zip_sha256':sha(zip_path.read_bytes()),'changed_paths':changed,'added_paths':added,'removed_paths':removed,'existing_png_count':len(pngs),'changed_existing_scripts':changed_scripts,'only_cold_config_change':'custom user directory isolation','original_config_sha256':original_config_sha,'review_config_sha256':sha(project.read_bytes())}
(review / 'incremental-integrity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key != 'checks'}, ensure_ascii=False))
