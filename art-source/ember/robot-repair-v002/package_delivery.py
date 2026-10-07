"""在冻结v004上添加修正版v002与证据，创建全新v005；旧ZIP不覆盖。"""
from pathlib import Path
import hashlib
import json
import zipfile
from finalize_repair import ROOT, PROOF, CATALOG, read, sha

DELIVERIES = ROOT / 'art-source/ember/deliveries'
BASE = DELIVERIES / 'ember_assets_v004_2026-10-04.zip'
TARGET = DELIVERIES / 'ember_assets_v005_2026-10-04.zip'


def main():
    if TARGET.exists(): raise FileExistsError('Preserve the existing release: ' + str(TARGET))
    acceptance = read(PROOF / 'final-acceptance.json')
    assert acceptance['status'] == 'ROBOT_V002_REPAIR_FINAL_ACCEPTANCE_PASS'
    assert sha(CATALOG) == acceptance['accepted_catalog_sha256']
    for field in ['evidence_sha256', 'delivery_document_sha256']:
        for name, expected in acceptance[field].items(): assert sha(ROOT / name) == expected, name
    baseline = read(PROOF / 'protected-before.json')
    for name, expected in baseline['sha256'].items():
        if name not in baseline['allowed_document_updates']: assert sha(ROOT / name) == expected, name
    assert sha(BASE) == acceptance['frozen_previous_archives'][BASE.relative_to(ROOT).as_posix()]
    payload = {}
    with zipfile.ZipFile(BASE) as archive:
        assert archive.testzip() is None
        previous = json.loads(archive.read('DELIVERY-MANIFEST.json'))
        for name, expected in previous['files'].items():
            data = archive.read(name)
            assert hashlib.sha256(data).hexdigest() == expected, name
            payload[name] = data
    # 旧载荷逐字节继承，只更新明确授权的两个文档入口和包内最小工程。
    for directory in [ROOT / 'assets/ember', ROOT / 'scenes/ember', PROOF,
                      ROOT / 'art-source/ember/quality-audit-2026-10-04']:
        for path in directory.rglob('*'):
            if not path.is_file(): continue
            if any(p.startswith('fresh-project-') or p in {'.godot', '__pycache__'} for p in path.parts): continue
            if path.suffix == '.pyc': continue
            name = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            if name in payload and name not in baseline['allowed_document_updates']:
                assert payload[name] == data, 'Unapproved inherited-file replacement: ' + name
            payload[name] = data
    for name in ['tools/build_ember_robot_animation_v002.gd', 'tools/build_ember_robot_animation_v002.gd.uid',
                 'docs/shader-learning/asset-production-robot-repair-v002.md', *baseline['allowed_document_updates']]:
        payload[name] = (ROOT / name).read_bytes()
    payload['project.godot'] = b'''config_version=5
[application]
config/name="Ember reusable assets v005 - Robot v002 repaired"
run/main_scene="res://scenes/ember/robot_animation_sandbox_v002.tscn"
[display]
window/size/viewport_width=1280
window/size/viewport_height=800
[rendering]
renderer/rendering_method="gl_compatibility"
'''
    files = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())}
    actual = (sum(n.startswith('assets/ember/') and n.endswith('.png') for n in files),
              sum(n.startswith('assets/ember/') and n.endswith('.tres') for n in files),
              sum(n.startswith('scenes/ember/') and n.endswith('.tscn') for n in files))
    assert actual == (122, 17, 5), actual
    manifest = {'date': '2026-10-04', 'revision': 'v005', 'completed_art_units': 123, 'remaining_art_units': 0,
        'completed_technical_inputs': 40, 'actual_layout_masks': 0, 'layout_mask_budget_upper_bound': 30,
        'production_png_files': 122, 'art_png_files_including_retained_versions': 82, 'technical_png_files': 40,
        'resource_files': 17, 'editable_scenes': 5,
        'current_recommended_version_files': {'production_pngs': 105, 'resources': 16, 'scenes': 4},
        'actual_archived_master_outputs': 77, 'new_imagegen_calls': 0, 'additional_art_units': 0,
        'active_robot_catalog': CATALOG.relative_to(ROOT).as_posix(),
        'active_robot_sprite_frames': 'assets/ember/characters/robot/robot_sprite_frames_v002.tres',
        'active_robot_scene': 'scenes/ember/robot_animation_sandbox_v002.tscn',
        'active_robot_frames': {'unchanged_v001_idle': 4, 'v002_walk': 16, 'v002_atlas': 1},
        'superseded_robot_v001': 'Retained as historical evidence. Three detached-pixel issues and five joint-seam candidates were identified after its original review. Use v002 for new layouts.',
        'base_archive_sha256': sha(BASE),
        'frozen_previous_archives': {Path(name).name: digest for name, digest in acceptance['frozen_previous_archives'].items()},
        'robot_repair_acceptance': 'art-source/ember/robot-repair-v002/final-acceptance.json',
        'robot_repair_acceptance_sha256': sha(PROOF / 'final-acceptance.json'),
        'historical_proofs': 'Older reports refer to frozen releases. Latest robot repair uses the new acceptance; unchanged technical inputs retain v004 acceptance.',
        'files': files}
    with zipfile.ZipFile(TARGET, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()): archive.writestr(name, data)
        archive.writestr('DELIVERY-MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    summary = {'status': 'FULL_ART_TECHNICAL_AND_ROBOT_REPAIR_V005_PACKAGED', 'file': TARGET.relative_to(ROOT).as_posix(),
        'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'payload_files': len(files),
        'production_pngs_including_retained_versions': 122, 'resources': 17, 'scenes': 5,
        'art_units': 123, 'technical_inputs': 40, 'active_robot_revision': 'v002'}
    TARGET.with_suffix('.package.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__': main()
