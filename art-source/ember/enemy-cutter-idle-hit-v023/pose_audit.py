"""Check fixed planted feet, bounded body response, and real reset frames."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[]
for clip in catalog['clips']:
    if clip['direction']=='down':continue
    kind=clip['action'].split('_')[0];poses=clip['poses'];first=poses[0]
    frames=[Image.open(ROOT/f'output/enemy_cutter/{clip["action"]}/f{i:02}.png').convert('RGBA') for i in range(4)]
    reset_index=2 if kind=='idle' else 3
    reset_equal=frames[0].tobytes()==frames[reset_index].tobytes()
    for i,pose in enumerate(poses):
        parts_unchanged=all(t==first['part_transforms'][name] for name,t in pose['part_transforms'].items() if name!='body')
        sole_fixed=pose['supports']==first['supports']
        actual_alpha=[]
        for name,support in pose['supports'].items():
            if support['sole'] is None:continue
            x,y=map(int,support['sole']);actual_alpha.append(dict(id=name,alpha=frames[i].getpixel((x,y-1))[3]))
        body_expected=pose['body_translation']==spec['actions'][kind]['body'][i]
        passed=parts_unchanged and sole_fixed and body_expected and reset_equal and all(x['alpha']==255 for x in actual_alpha)
        records.append(dict(action=clip['action'],frame=i,legs_unchanged=parts_unchanged,sole_fixed=sole_fixed,body_expected=body_expected,reset_frame_equal=reset_equal,actual_sole_alpha=actual_alpha,passed=passed))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),records=records)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],records=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(not passed)
