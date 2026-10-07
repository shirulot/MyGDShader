"""Read-only checks of exported endpoints, real floor bounds, and rigid transforms."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[]
for clip in catalog['clips']:
 frames=[Image.open(ROOT/'output/enemy_cutter'/clip['action']/f'f{i:02}.png').convert('RGBA') for i in range(clip['frame_count'])]
 kind=clip['action'].split('_')[0]
 endpoint=frames[0].tobytes()==frames[-1].tobytes() if kind=='attack' else len({im.tobytes() for im in frames[-3:]})==1
 # 正向已通过图按原字节继承，其攻击前伸工具超过root行；新图单独检验。
 floor=clip['status']=='PRESERVED_TA_APPROVED' or all(im.getchannel('A').getbbox()[3]<=104 for im in frames)
 rigid=True;fixed_feet=True;blade_area=True
 for pose in clip['poses']:
  for name,t in pose['part_transforms'].items():
   x,y=t['basis_x'],t['basis_y'];det=x[0]*y[1]-x[1]*y[0]
   if name.endswith('_blade'):blade_area &= abs(det-1)<1e-5
   else:rigid &= abs(math.hypot(*x)-1)<1e-5 and abs(math.hypot(*y)-1)<1e-5 and abs(x[0]*y[0]+x[1]*y[1])<1e-5
   if name.endswith('_foot'):fixed_feet &= t==dict(position=[0,0],basis_x=[1,0],basis_y=[0,1])
 config=spec['configs'].get(clip['direction'])
 source_ok=config is None or sha(ROOT/config['source'].removeprefix('res://'))==config['source_sha256']
 records.append(dict(action=clip['action'],endpoint_equal=endpoint,floor_y_max=max(im.getchannel('A').getbbox()[3] for im in frames),fixed_foot_transforms=fixed_feet,rigid_armor=rigid,blade_projected_area_preserved=blade_area,source_hash_exact=source_ok,passed=all([endpoint,floor,rigid,fixed_feet,blade_area,source_ok])))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),records=records,limits='Fixed foot transforms do not prove every sole probe remains visible: body/tool occlusion is retained. Each source pixel has one owner; hidden joint quads instance registered source colors and may expose additional output pixels. GPU roundtrip is checked separately.')
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],actions=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(0 if passed else 1)
