"""Actual support, rigid caps/boots, tool pixel and connector endpoint checks."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
records=[]
for clip in catalog['clips']:
    if clip['direction'] not in spec['configs']:continue
    cfg=spec['configs'][clip['direction']]
    src=Image.open(ROOT/cfg['source'].removeprefix('res://')).convert('RGBA')
    tool_pixels=[(x,y) for y in range(128) for x in range(128) if src.getpixel((x,y))[3] and any(inside((x+.5,y+.5),p) for p in cfg['protected_body_polygons'])]
    for i,pose in enumerate(clip['poses']):
        frame=Image.open(ROOT/clip['atlas'].removeprefix('res://')).crop((128*i,0,128*(i+1),128)).convert('RGBA')
        bob=spec['phases'][i]['body_y']
        changed=[(x,y) for x,y in tool_pixels if src.getpixel((x,y))!=frame.getpixel((x,y+bob))]
        rigid=True;errors=[]
        for p in cfg['parts']:
            t=pose['part_transforms'][p['id']]
            if p['id'].endswith(('_cap','_foot')):
                rigid &= t['basis_x']==[1,0] and t['basis_y']==[0,1]
                continue
            leg=cfg['legs'][p['id'].split('_')[0]];actual=pose['supports'][p['id'].split('_')[0]]
            anchor='knee' if p['id'].endswith('_thigh') else 'ankle'
            expected=[actual[anchor][j]+p['end'][j]-leg[anchor][j] for j in [0,1]]
            delta=[p['end'][j]-p['pivot'][j] for j in [0,1]]
            mapped=[t['position'][j]+delta[0]*t['basis_x'][j]+delta[1]*t['basis_y'][j] for j in [0,1]]
            errors.append(math.dist(mapped,expected))
        support=all(not v['support'] or math.dist(v['sole'],v['ground'])<1e-6 for v in pose['supports'].values())
        endpoint=max(errors)<1e-4
        records.append(dict(action=clip['action'],frame=i,protected_tool_pixels=len(tool_pixels),changed_tool_pixels=changed,rigid_caps_boots=rigid,support_sole_matches_ground=support,connector_max_error=max(errors),passed=not changed and rigid and support and endpoint))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),records=records)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],records=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(not passed)
