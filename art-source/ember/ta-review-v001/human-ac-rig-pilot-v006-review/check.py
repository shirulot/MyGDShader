"""只读候选，保存独立快照并复核实际导出和记录的姿态。"""
from pathlib import Path
from PIL import Image
import hashlib
import json
import math
import shutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / 'human-ac-rig-pilot-v006'
entries = []
for path in sorted(SOURCE.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(SOURCE)
    data = path.read_bytes()
    target = HERE / 'submitted' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data, f'Frozen snapshot changed: {relative}'
    else:
        shutil.copyfile(path, target)
    entries.append({'path': relative.as_posix(), 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest()})
manifest = (json.dumps(entries, ensure_ascii=False, indent=2) + '\n').encode()
(HERE / 'source-manifest.json').write_bytes(manifest)
snap = HERE / 'submitted'
meta = json.loads((snap / 'final/A-walk-down_right-rig-v006.json').read_text(encoding='utf-8'))
atlas = Image.open(snap / 'final/A-walk-down_right-rig-v006.png').convert('RGBA')
assert atlas.size == (512, 96)
assert meta['frame_size'] == [64, 96] and meta['root'] == [32, 80]
assert meta['duration_ms'] == [120] * 8 and meta['loop'] is True
assert set(atlas.getchannel('A').getdata()) == {0, 255}
frames = [atlas.crop((i*64, 0, (i+1)*64, 96)) for i in range(8)]
assert len({im.tobytes() for im in frames}) == 8
contact = Image.open(snap / 'qa/contact.png').convert('RGBA')
assert contact.tobytes() == atlas.resize((2048,384), Image.Resampling.NEAREST).tobytes()
assert hashlib.sha256((snap / meta['source']).read_bytes()).hexdigest() == meta['source_sha256']
poses = json.loads((snap / 'qa/poses.json').read_text(encoding='utf-8'))
errors = []
support = {}
for side in ('near', 'far'):
    points = []
    for i, pose in enumerate(poses):
        q = pose[side]
        for a,b,length in [('hip','knee',12),('knee','ankle',11),('shoulder','elbow',9),('elbow','wrist',12)]:
            errors.append(abs(math.dist(q[a],q[b])-length))
        if q['support']:
            points.append([q['ankle'][0]+3*i,q['ankle'][1]+1.05*i])
    support[side] = {'positions': points,
                     'max_distance_from_first': max(math.dist(points[0], p) for p in points)}
result = {'scope':'export_and_recorded_pose_checks_only', 'files':len(entries),
          'source_manifest_sha256':hashlib.sha256(manifest).hexdigest(),
          'frames':8, 'colors':len({p[:3] for p in atlas.getdata() if p[3]}),
          'maximum_recorded_bone_length_error':max(errors), 'support_samples':support,
          'continuous_foot_lock_tested':False, 'godot_tested':False,
          'reexecuted_renderer':False, 'production_ready':False}
(HERE/'technical.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
