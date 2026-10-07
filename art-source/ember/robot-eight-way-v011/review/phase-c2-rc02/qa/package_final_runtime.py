"""资源路径实测通过后再打包精简交付，排除本机Godot缓存和临时日志。"""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
release = root / 'delivery/robot-v011'
report = json.loads((release / 'evidence/runtime-import-validation.json').read_text(encoding='utf-8'))
if report['technical_checks'] != 'PASS' or report['checked_frames'] != 112 or report['errors']:
    raise ValueError('Runtime import has not passed')
archive = root.parent / 'deliveries/robot_eight_way_v011_final_2026-10-07.zip'
if archive.exists() or (release / 'sha256-manifest.json').exists():
    raise FileExistsError('Final release is already frozen')
digest = lambda data: hashlib.sha256(data).hexdigest()
files = sorted(file for file in release.rglob('*') if file.is_file() and '.godot' not in file.parts and file.suffix != '.log')
catalog = {'status': 'TA_ACCEPTED', 'clips': 24, 'frames': 112, 'atlas_sha256': report['atlas_sha256'],
           'files': [{'file': file.relative_to(release).as_posix(), 'bytes': file.stat().st_size, 'sha256': digest(file.read_bytes())} for file in files]}
manifest = release / 'sha256-manifest.json'
manifest.write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as pack:
    for file in files + [manifest]:
        pack.write(file, file.relative_to(release).as_posix())
with zipfile.ZipFile(archive) as pack:
    for item in catalog['files']:
        if digest(pack.read(item['file'])) != item['sha256']:
            raise ValueError('Packaged file changed: ' + item['file'])
receipt = {'status': 'PASS', 'zip': str(archive), 'zip_bytes': archive.stat().st_size, 'zip_sha256': digest(archive.read_bytes()),
           'payload_files': len(files), 'zip_entries': len(files) + 1, 'sha256_manifest_sha256': digest(manifest.read_bytes()),
           'atlas_sha256': report['atlas_sha256'], 'clips': 24, 'frames': 112, 'runtime_import': 'PASS', 'payload_hash_mismatches': 0}
(root / 'qa/final-runtime-delivery.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
