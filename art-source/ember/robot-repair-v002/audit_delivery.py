"""只读验收v005载荷及完整继承，包外记录结果，不改历史交付。"""
import hashlib
import json
import re
import zipfile
from io import BytesIO
from PIL import Image
from finalize_repair import ROOT, PROOF, CATALOG, read, sha
from package_delivery import BASE, TARGET


def main():
    acceptance = read(PROOF / 'final-acceptance.json')
    baseline = read(PROOF / 'protected-before.json')
    catalog = read(CATALOG)
    checks = []

    def check(name, passed): checks.append({'check': name, 'pass': bool(passed)})

    check('accepted current catalog', sha(CATALOG) == acceptance['accepted_catalog_sha256'])
    for field in ['evidence_sha256', 'delivery_document_sha256']:
        for name, expected in acceptance[field].items(): check('current accepted evidence ' + name, sha(ROOT / name) == expected)
    for name, expected in baseline['sha256'].items():
        if name not in baseline['allowed_document_updates']: check('current prior protected ' + name, sha(ROOT / name) == expected)
    with zipfile.ZipFile(BASE) as previous_zip, zipfile.ZipFile(TARGET) as archive:
        check('ZIP CRC', archive.testzip() is None)
        manifest = json.loads(archive.read('DELIVERY-MANIFEST.json'))
        files = manifest['files']
        check('unique entries', len(archive.namelist()) == len(set(archive.namelist())))
        check('payload manifest complete', set(archive.namelist()) == set(files) | {'DELIVERY-MANIFEST.json'})
        for name, expected in files.items(): check('payload SHA ' + name, hashlib.sha256(archive.read(name)).hexdigest() == expected)
        previous = json.loads(previous_zip.read('DELIVERY-MANIFEST.json'))
        allowed = set(baseline['allowed_document_updates']) | {'project.godot'}
        for name, expected in previous['files'].items():
            if name not in allowed: check('unchanged v004 inherited payload ' + name, files.get(name) == expected)
        for field in ['evidence_sha256', 'delivery_document_sha256']:
            for name, expected in acceptance[field].items(): check('ZIP accepted evidence ' + name, files.get(name) == expected)
        check('accepted proof exact', archive.read('art-source/ember/robot-repair-v002/final-acceptance.json') == (PROOF / 'final-acceptance.json').read_bytes())
        check('manifest binds acceptance', manifest['robot_repair_acceptance_sha256'] == sha(PROOF / 'final-acceptance.json'))
        check('ZIP catalog exact', archive.read(CATALOG.relative_to(ROOT).as_posix()) == CATALOG.read_bytes())
        atlas = Image.open(BytesIO(archive.read(catalog['sheet']['texture'].removeprefix('res://')))).convert('RGBA')
        for frame in catalog['frames']:
            name = frame['file'].removeprefix('res://')
            check('ZIP robot source ' + frame['id'], files.get(name) == frame['sha256'])
            source = Image.open(BytesIO(archive.read(name))).convert('RGBA')
            x, y = frame['coord']
            check('ZIP robot atlas crop ' + frame['id'], atlas.crop((x * 64, y * 96, (x + 1) * 64, (y + 1) * 96)).tobytes() == source.tobytes())
        for name, expected in catalog['repair_dependency_sha256'].items(): check('ZIP editable-source dependency ' + name, files.get(name) == expected)
        # 所有本包资源引用都必须落在包内，避免仅在原项目缓存中可用。
        for name in files:
            if name.startswith(('assets/ember/', 'scenes/ember/')) and name.endswith(('.tres', '.tscn')):
                refs = re.findall(r'path="(res://[^"]+)"', archive.read(name).decode('utf-8'))
                for ref in refs: check('resource dependency ' + name + ' ' + ref, ref.removeprefix('res://') in files)
        actual = (sum(n.startswith('assets/ember/') and n.endswith('.png') for n in files),
                  sum(n.startswith('assets/ember/') and n.endswith('.tres') for n in files),
                  sum(n.startswith('scenes/ember/') and n.endswith('.tscn') for n in files))
        check('actual 122/17/5 including retained versions', actual == (122, 17, 5))
        check('logical 123 art / 40 tech / 0 layouts', (manifest['completed_art_units'], manifest['completed_technical_inputs'], manifest['actual_layout_masks']) == (123, 40, 0))
        check('v002 default scene / no autoload', b'run/main_scene="res://scenes/ember/robot_animation_sandbox_v002.tscn"' in archive.read('project.godot') and b'[autoload]' not in archive.read('project.godot'))
        check('no caches / fresh-copy directories', not any('.godot' in n.split('/') or '__pycache__' in n.split('/') or any(p.startswith('fresh-project-') for p in n.split('/')) for n in files))
    failures = [c['check'] for c in checks if not c['pass']]
    result = {'status': 'V005_ROBOT_REPAIR_AND_FULL_DELIVERY_ZIP_AUDIT_PASS' if not failures else 'V005_AUDIT_FAIL',
        'checks': len(checks), 'failed_checks': len(failures), 'failures': failures, 'zip_sha256': sha(TARGET),
        'art_units': 123, 'technical_inputs': 40, 'production_pngs_including_retained_versions': 122,
        'resources': 17, 'scenes': 5, 'active_robot_revision': 'v002', 'prior_protected_files': len(baseline['sha256']),
        'results': checks}
    TARGET.with_suffix('.audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}, ensure_ascii=False))
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
