"""Validate actual reset frames, planted boots and rigid caps against pose records."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[]
for clip in catalog['clips']:
 if clip['direction']=='down':continue
 kind=clip['action'].split('_')[0];poses=clip['poses'];first=poses[0]
 images=[Image.open(ROOT/'output/enemy_patrol'/clip['action']/f'f{i:02}.png').convert('RGBA') for i in range(4)]
 reset=images[0].tobytes()==images[2 if kind=='idle' else 3].tobytes()
 for i,pose in enumerate(poses):
  feet=all(t==first['part_transforms'][name] for name,t in pose['part_transforms'].items() if name.endswith('_foot'))
  caps=all(t['basis_x']==[1,0] and t['basis_y']==[0,1] for name,t in pose['part_transforms'].items() if name.endswith('_cap'))
  support=all(v['sole']==v['ground'] and v['sole']==first['supports'][side]['sole'] for side,v in pose['supports'].items())
  delta=pose['body_translation']==spec['actions'][kind]['body'][i]
  records.append(dict(action=clip['action'],frame=i,fixed_foot_transforms=feet,rigid_knee_caps=caps,support_fixed=support,body_expected=delta,reset_frame_equal=reset,passed=all([feet,caps,support,delta,reset])))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),records=records,limits='Fixed support transforms do not prove all original support pixels remain visible under overlapping parts; final visual and GPU checks are separate.')
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],records=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(not passed)
