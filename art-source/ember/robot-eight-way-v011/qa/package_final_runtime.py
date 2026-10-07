"""资源路径实测通过后再打包精简交付，排除本机Godot缓存和临时日志。"""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
candidate = '--candidate' in sys.argv[1:]
release = root / ('delivery/robot-v011-candidate-v2' if candidate else 'delivery/robot-v011')
report = json.loads((release / 'evidence/runtime-import-validation.json').read_text(encoding='utf-8'))
if report['technical_checks'] != 'PASS' or report['checked_frames'] != 112 or report['errors']:
    raise ValueError('Runtime import has not passed')
import_receipt = json.loads((release / 'evidence/runtime-editor-import.json').read_text(encoding='utf-8'))
if any(import_receipt[key] != 0 for key in ['import_exit_code','import_stderr_bytes','verify_exit_code','verify_stderr_bytes']):
    raise ValueError('Godot editor import or verifier reported errors')
metadata = json.loads((release / 'full-action-metadata.json').read_text(encoding='utf-8'))
if not candidate and metadata['status'] != 'ALL_24_CLIPS_112_FRAMES_TA_ACCEPTED':
    raise ValueError('Final art acceptance is required for final packaging')
if not candidate:
    # 正式包的路径变化必须有新入口运行和逐文件来源映射，不能只借用旧项目的通过记录。
    entry = json.loads((release / 'evidence/runtime-entry-validation.json').read_text(encoding='utf-8'))
    migration = json.loads((release / 'evidence/runtime-migration-validation.json').read_text(encoding='utf-8'))
    if any(import_receipt[key] != 0 for key in ['entry_exit_code', 'entry_stderr_bytes']):
        raise ValueError('Actual GPU entry reported errors')
    if entry['technical_checks'] != 'PASS' or entry['errors'] or migration['technical_checks'] != 'PASS' or migration['errors']:
        raise ValueError('Runtime entry or migration has not passed')
    if migration['unchanged_frame_pngs'] != 112 or migration['unchanged_animation_files'] != 192:
        raise ValueError('Runtime source mapping is incomplete')
archive = root.parent / 'deliveries' / ('robot_eight_way_v011_candidate_c2_rc02_v2_2026-10-07.zip' if candidate else 'robot_eight_way_v011_final_2026-10-07.zip')
if archive.exists() or (release / 'sha256-manifest.json').exists():
    raise FileExistsError('Final release is already frozen')
digest = lambda data: hashlib.sha256(data).hexdigest()
files = sorted(file for file in release.rglob('*') if file.is_file() and '.godot' not in file.parts and file.suffix != '.log')
catalog = {'status': 'CANDIDATE_NEW_42_PENDING_TA' if candidate else 'TA_ACCEPTED', 'clips': 24, 'frames': 112, 'atlas_sha256': report['atlas_sha256'],
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
receipt = {'status': 'TECHNICAL_PASS_ART_PENDING' if candidate else 'PASS', 'zip': str(archive), 'zip_bytes': archive.stat().st_size, 'zip_sha256': digest(archive.read_bytes()),
           'payload_files': len(files), 'zip_entries': len(files) + 1, 'sha256_manifest_sha256': digest(manifest.read_bytes()),
           'atlas_sha256': report['atlas_sha256'], 'clips': 24, 'frames': 112, 'runtime_import': 'PASS', 'payload_hash_mismatches': 0}
(root / ('qa/candidate-runtime-delivery.json' if candidate else 'qa/final-runtime-delivery.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
