"""从最终ZIP创建全新独立工程，验证导入及实际GPU入口；记录写包外。"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
delivery = json.loads((root / 'qa/final-runtime-delivery.json').read_text(encoding='utf-8'))
archive = Path(delivery['zip'])
frozen = root / 'delivery/robot-v011'
cold = root / 'review/cold-runtime-final'
output = root / 'qa/cold-runtime-final-validation'
godot = Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes()) == delivery['zip_sha256']
if cold.exists() or output.exists():
    raise FileExistsError('Cold validation already exists; preserve its evidence')

with zipfile.ZipFile(archive) as pack:
    for name in pack.namelist():
        member = PurePosixPath(name)
        assert not member.is_absolute() and '..' not in member.parts and ':' not in name
    catalog = json.loads(pack.read('sha256-manifest.json'))
    assert sha(pack.read('sha256-manifest.json')) == delivery['sha256_manifest_sha256']
    for item in catalog['files']:
        assert sha(pack.read(item['file'])) == item['sha256'], item['file']
    pack.extractall(cold)
assert not (cold / '.godot').exists()
output.mkdir(parents=True)
process_results = {}
commands = {
    'import': ['--headless', '--editor', '--import'],
    'verify': ['--headless', '--script', 'res://verify_import.gd'],
    'entry': ['--script', 'res://verify_entry.gd'],
}
for label, args in commands.items():
    # 窗口隐藏运行检查进程，不触碰用户已打开的Godot编辑器。
    stdout = output / (label + '.log')
    stderr = output / (label + '-error.log')
    with stdout.open('wb') as out, stderr.open('wb') as err:
        result = subprocess.run([str(godot), '--path', str(cold), *args], stdout=out, stderr=err,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                timeout=50, check=False)
    process_results[label] = {'exit_code': result.returncode, 'stderr_bytes': stderr.stat().st_size}
    assert result.returncode == 0 and stderr.stat().st_size == 0, process_results[label]

load_report = json.loads((cold / 'evidence/runtime-import-validation.json').read_text(encoding='utf-8'))
entry_report = json.loads((cold / 'evidence/runtime-entry-validation.json').read_text(encoding='utf-8'))
assert load_report['technical_checks'] == 'PASS' and load_report['checked_frames'] == 112 and not load_report['errors']
assert entry_report['technical_checks'] == 'PASS' and not entry_report['errors']
changed = []
for folder_name, folder in [('frozen', frozen), ('cold', cold)]:
    assert sha((folder / 'sha256-manifest.json').read_bytes()) == delivery['sha256_manifest_sha256']
    for item in catalog['files']:
        if sha((folder / item['file']).read_bytes()) != item['sha256']:
            changed.append(folder_name + '/' + item['file'])
report = {'technical_checks': 'PASS' if not changed else 'FAIL', 'zip_sha256': delivery['zip_sha256'],
          'cold_root': str(cold), 'payload_files': len(catalog['files']), 'process_results': process_results,
          'checked_frames': load_report['checked_frames'], 'clips': load_report['clips'],
          'entry_validation': entry_report, 'payload_changes_after_engine': changed,
          'scope': 'Fresh final ZIP import and minimum actual GPU entry; not a repeat of the old full 224-sample matrix'}
(output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
assert not changed, changed
