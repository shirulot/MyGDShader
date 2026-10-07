"""将浏览器输出的固定格 PNG 包装为预览和验证记录；不修改角色绘画。"""
from pathlib import Path
from PIL import Image
import hashlib
import json

root = Path(__file__).resolve().parent
sheet = Image.open(root / 'final/A-walk-down_right-gait-v008.png').convert('RGBA')
frames = [sheet.crop((i * 64, 0, (i + 1) * 64, 96)) for i in range(8)]
large = [f.resize((256, 384), Image.Resampling.NEAREST) for f in frames]
large[0].save(root / 'previews/A-walk-down_right.webp', save_all=True,
              append_images=large[1:], duration=120, loop=0, lossless=True)
sheet.resize((2048, 384), Image.Resampling.NEAREST).save(root / 'qa/contact.png')
report = {
    'cell': [64, 96], 'root': [32, 80], 'frame_count': 8,
    'alpha': sorted(set(sheet.getchannel('A').getdata())),
    'colors': len({c[:3] for c in sheet.getdata() if c[3]}),
    'unique_frames': len({f.tobytes() for f in frames}),
    'bboxes': [f.getbbox() for f in frames],
    'end_duplicate': frames[0].tobytes() == frames[-1].tobytes(),
}
assert report['alpha'] == [0, 255] and report['colors'] <= 18
assert report['unique_frames'] == 8 and not report['end_duplicate']
assert all(b[0] > 0 and b[1] > 0 and b[2] < 64 and b[3] < 96 for b in report['bboxes'])
(root / 'qa/export-check.json').write_text(json.dumps(report, indent=2))
meta = {
    'id': 'A-walk-down_right-gait-v008', 'parent': 'human-ac-knee-v007',
    'production_ready': False, 'loop': True, 'playback': 'forward',
    'duration_ms': [120] * 8, 'cell': [64, 96], 'root': [32, 80],
    'world_displacement_per_cycle': [13, 4.6],
    'source_sha256': hashlib.sha256((root / 'source/A-parts.png').read_bytes()).hexdigest(),
    'method': 'same static parts; sagittal-plane IK then oblique projection; registered mounts',
    'runtime_status': 'not_tested_in_godot', 'visual_status': 'candidate_pending_review',
    'mounts': 'qa/mounts.json', 'poses': 'qa/poses.json',
}
(root / 'run-manifest.json').write_text(json.dumps(meta, indent=2))
(root / 'final/A-walk-down_right-gait-v008.json').write_text(json.dumps(meta, indent=2))
print(json.dumps(report))
