"""Read-only rendered endpoint and ground-plane checks, bound to this catalog."""
from pathlib import Path
from PIL import Image
import json,hashlib
ROOT=Path(__file__).resolve().parent
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
records=[]
for clip in catalog['clips']:
    path=ROOT/'output/enemy_scout_drone'/clip['action']
    frames=[Image.open(path/f'f{i:02}.png').convert('RGBA') for i in range(clip['frame_count'])]
    if clip['action'].startswith('attack_'):
        okay=frames[0].tobytes()==frames[-1].tobytes()
        records.append(dict(action=clip['action'],attack_restored_rgba=okay,passed=okay))
    else:
        boxes=[im.getchannel('A').getbbox() for im in frames]
        held=all(frames[i].tobytes()==frames[7].tobytes() for i in [5,6])
        ground=boxes[7][3]==104
        monotone=all(a[3]<=b[3] for a,b in zip(boxes,boxes[1:]))
        records.append(dict(action=clip['action'],bottom_edges=[b[3] for b in boxes],held_last_three_frames=held,ground_edge_104=ground,passed=held and ground and monotone))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=hashlib.sha256((ROOT/'output/catalog.json').read_bytes()).hexdigest(),records=records)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
raise SystemExit(0 if passed else 1)
