"""核对已冻结源包到精简运行包的搬运；不修改任何已通过图像。"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[1]
runtime = root / 'delivery/robot-v011'
gate = json.loads((root / 'qa/final-release-gate.json').read_text(encoding='utf-8'))
source = root / 'review' / gate['source_revision']
digest = lambda data: hashlib.sha256(data).hexdigest()
read_json = lambda file: json.loads(file.read_text(encoding='utf-8'))
source_manifest = read_json(source / 'sha256-manifest.json')
assert digest((source / 'sha256-manifest.json').read_bytes()) == gate['source_manifest_sha256']
assert digest((source / 'full-action-metadata.json').read_bytes()) == gate['source_metadata_sha256']

# 先确认审查对象未改变，避免拿工作区的新内容替代已获批的固定源包。
for item in source_manifest['files']:
    assert digest((source / item['file']).read_bytes()) == item['sha256'], item['file']
meta = read_json(source / 'full-action-metadata.json')
new_meta = read_json(runtime / 'full-action-metadata.json')
atlas = meta['atlas']
asset_folder = 'assets/ember/robot_v011'
mapping = []

def unchanged(source_name, runtime_name, kind):
    old = (source / source_name).read_bytes()
    new = (runtime / runtime_name).read_bytes()
    assert new == old, runtime_name
    mapping.append({'source': source_name, 'runtime': runtime_name, 'kind': kind,
                    'result': 'BYTE_IDENTICAL', 'sha256': digest(new)})

for clip in meta['clips']:
    for frame in clip['frames']:
        unchanged(frame['file'], frame['file'], 'frame_png')
unchanged(atlas, asset_folder + '/' + atlas, 'atlas_png')
animations = read_json(source / 'qa/full_action_animated_exports.json')
for item in animations:
    unchanged(item['file'], item['file'], 'animated_preview')

def path_only(source_name, runtime_name, old_path, new_path):
    original = (source / source_name).read_bytes()
    expected = original.replace(old_path.encode(), new_path.encode())
    actual = (runtime / runtime_name).read_bytes()
    assert original != expected and actual == expected, runtime_name
    mapping.append({'source': source_name, 'runtime': runtime_name, 'kind': 'resource_path',
                    'result': 'ONLY_DECLARED_PATH_REPLACEMENT', 'old_path': old_path,
                    'new_path': new_path, 'source_sha256': digest(original),
                    'runtime_sha256': digest(actual)})

path_only('godot-full-review/robot_eight_way_v011.tres', asset_folder + '/robot_eight_way_v011.tres',
          'res://assets/' + atlas, 'res://' + asset_folder + '/' + atlas)
path_only('godot-full-review/preview_full_actions.gd', 'preview/preview_full_actions.gd',
          'res://robot_eight_way_v011.tres', 'res://' + asset_folder + '/robot_eight_way_v011.tres')
path_only('godot-full-review/preview_full_actions.tscn', 'preview/preview_full_actions.tscn',
          'res://preview_full_actions.gd', 'res://preview/preview_full_actions.gd')
path_only('godot-full-review/project.godot', 'project.godot',
          'res://preview_full_actions.tscn', 'res://preview/preview_full_actions.tscn')

# Godot根据资源路径重建缓存文件名；导入器选项、UID及其余字段仍须相同。
old_import = (source / ('godot-full-review/assets/' + atlas + '.import')).read_text(encoding='utf-8')
new_import = (runtime / (asset_folder + '/' + atlas + '.import')).read_text(encoding='utf-8')
old_cache = re.search(r'^path="([^"]+)"', old_import, re.M)[1]
new_cache = re.search(r'^path="([^"]+)"', new_import, re.M)[1]
expected_import = old_import.replace('res://assets/' + atlas, 'res://' + asset_folder + '/' + atlas).replace(old_cache, new_cache)
assert new_import == expected_import
assert new_import.split('[params]', 1)[1] == old_import.split('[params]', 1)[1]
assert 'process/fix_alpha_border=false' in new_import and 'mipmaps/generate=false' in new_import

# metadata只更新放行标签、atlas位置及回执；每个frame/region/fps/loop必须保持。
expected_meta = deepcopy(meta)
expected_meta.update(release='robot-v011-final', status='ALL_24_CLIPS_112_FRAMES_TA_ACCEPTED', atlas=asset_folder + '/' + atlas)
expected_meta['art_acceptance'] = {'receipt': 'evidence/ta-c2-final.md',
    'receipt_sha256': gate['ta_receipt_sha256'], 'approved_total_frames': 112,
    'original_candidate_metadata_sha256': gate['source_metadata_sha256'], 'candidate_pending': False}
for clip in expected_meta['clips']:
    clip['art_status'] = 'PASS'
assert new_meta == expected_meta
assert digest((runtime / 'evidence/ta-c2-final.md').read_bytes()) == gate['ta_receipt_sha256']

# 网页沿用同一播放实现，只改变已通过文案和独立工程链接。
old_html = (source / 'action-batch-review.html').read_text(encoding='utf-8')
expected_html = old_html.replace('八向行走与南西小样已通过；本次新增的七向待机、采集正在独立审查。', '八向待机、行走和采集已通过逐批独立审查。')
expected_html = expected_html.replace("clip.art_status==='PASS_RETAINED'?'保留已通过原帧':'新增动作待独立审查'", "clip.art_status==='PASS'?'已通过独立审查':'待审'").replace('godot-full-review/project.godot', 'project.godot')
assert (runtime / 'preview.html').read_text(encoding='utf-8') == expected_html
for folder in ['frames', 'previews', 'evidence']:
    assert (runtime / folder / '.gdignore').read_bytes() == b''

entry = read_json(runtime / 'evidence/runtime-entry-validation.json')
assert entry['technical_checks'] == 'PASS' and not entry['errors']
frame_count = sum(len(clip['frames']) for clip in meta['clips'])
assert frame_count == 112 and len(meta['clips']) == 24 and len(animations) == 192
report = {'technical_checks': 'PASS', 'source_revision': gate['source_revision'],
    'source_zip_sha256': gate['source_zip_sha256'], 'source_manifest_sha256': gate['source_manifest_sha256'],
    'source_payload_files_verified': len(source_manifest['files']), 'unchanged_frame_pngs': frame_count,
    'unchanged_atlas_pngs': 1, 'unchanged_animation_files': len(animations), 'path_only_resources': 4,
    'atlas_sha256': gate['atlas_sha256'], 'metadata_parameters_and_regions': 'UNCHANGED',
    'import_params': 'UNCHANGED', 'importer_changes': ['source_file path', 'path-derived cache locations'],
    'web_changes': ['acceptance labels', 'project link'], 'main_entry_actual_gpu': 'PASS',
    'new_files': ['README and joint rules', 'TA receipts and evidence', 'verification scripts and Godot UID sidecars', 'three .gdignore files'],
    'mapping': mapping, 'errors': []}
(runtime / 'evidence/runtime-migration-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(runtime / 'evidence/runtime-migration.md').write_text('''# 已审源包到正式运行包的迁移核对

来源：phase-c2-rc02；该固定源包全部1723载荷逐项校验通过。

112张帧PNG、同一张atlas和192个动画文件逐字节相同。SpriteFrames、预览脚本、场景、project.godot仅做已声明路径替换。每帧图集矩形、播放速度、循环参数和root均保持。

atlas导入设置保持，包含fix_alpha_border=false和mipmaps=false；Godot只根据新路径改写源路径及缓存路径。metadata和网页仅改变通过标签、证据绑定及资源链接。frames/previews/evidence通过.gdignore排除编辑器自动导入，verify_import仍从原PNG读取对照。

新工程入口已实际GPU运行：idle/walk自然循环、同相位换向、采集期间方向锁定、四帧单次完成后双显示节点回idle F00，1×/4×可见像素一致。完整旧源包224 GPU画面和全部方向矩阵的记录作为源包既有证据；此处新入口仅重跑迁移所需行为。

逐文件来源映射和哈希见runtime-migration-validation.json；新入口见runtime-entry-validation.json和runtime-entry-collect.png。本报告为制作方验证，独立迁移复审回执另行绑定最终ZIP。
''', encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key != 'mapping'}, ensure_ascii=False))
