"""独立保存候选字节并核对交付；不执行作者导出，不修改候选。"""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / 'human-ac-pose-pilot-v005'
snapshot = HERE / 'submitted'
entries = []
for path in sorted(SOURCE.rglob('*')):
    if not path.is_file():
        continue
    rel = path.relative_to(SOURCE)
    data = path.read_bytes()
    target = snapshot / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data, f'Frozen snapshot differs: {rel}'
    else:
        shutil.copyfile(path, target)
    entries.append({'path': rel.as_posix(), 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest()})
manifest_bytes = (json.dumps(entries, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
(HERE / 'source-manifest.json').write_bytes(manifest_bytes)
catalog = json.loads((snapshot / 'catalog.json').read_text(encoding='utf-8'))
results = []
for clip in catalog['clips']:
    count = clip['frame_count']
    assert clip['cell'] == [64, 96] and clip['root'] == [32, 80]
    atlas = Image.open(snapshot / clip['atlas']).convert('RGBA')
    assert atlas.size == (64 * count, 96)
    bboxes = []
    for index in range(count):
        frame = Image.open(snapshot / 'frames' / clip['key'] / f'f{index:02}.png').convert('RGBA')
        assert frame.size == (64, 96)
        assert set(frame.getchannel('A').getdata()) <= {0, 255}
        assert frame.tobytes() == atlas.crop((64 * index, 0, 64 * (index + 1), 96)).tobytes()
        bboxes.append(frame.getbbox())
    contact = Image.open(snapshot / 'qa' / f"{clip['key']}-contact.png").convert('RGBA')
    assert contact.tobytes() == atlas.resize((64 * count * 4, 384), Image.Resampling.NEAREST).tobytes()
    results.append({'key': clip['key'], 'frames': count, 'duration_ms': clip['duration_ms'],
                    'bboxes': bboxes, 'common_scale': clip['common_scale'],
                    'atlas_frame_rgba_match': True, 'contact_matches_atlas': True})
# 限定“局部编辑”保留范围是否逐字节保持；差异不自动等于某个造型缺陷。
edit_results = []
for key in ('A-walk-down_right', 'C-run-down_left'):
    before = Image.open(snapshot / 'source' / f'{key}.png').convert('RGBA')
    after = Image.open(snapshot / 'source' / f'{key}-r2-rejected.png').convert('RGBA')
    assert before.size == after.size
    rect = (0, 0, before.width, before.height // 2)
    left = before.crop(rect)
    right = after.crop(rect)
    changed = sum(a != b for a, b in zip(left.getdata(), right.getdata()))
    edit_results.append({'key': key, 'top_half_changed_rgba_pixels': changed,
                         'top_half_total_pixels': left.width * left.height})
result = {'scope': 'export_and_source_binding_only', 'files': len(entries),
          'source_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
          'clips': results, 'rejected_edit_preservation': edit_results,
          'runtime_status': 'not_reviewed', 'production_ready': False}
(HERE / 'technical.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
