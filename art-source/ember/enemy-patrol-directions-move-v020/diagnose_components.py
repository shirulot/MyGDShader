"""Read-only component/source attribution for local registration repairs."""
from pathlib import Path
from PIL import Image
import json,math
ROOT=Path(__file__).resolve().parent
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
for clip in catalog['clips']:
    if clip['direction'] not in spec['configs']:continue
    cfg=spec['configs'][clip['direction']]
    src=Image.open(ROOT/cfg['source'].removeprefix('res://')).convert('RGBA')
    parts=[dict(id='body',pivot=[0,0],z=5,polygon=[],exclude=[p['polygon'] for p in cfg['parts']])]+cfg['parts']
    for i,pose in enumerate(clip['poses']):
        im=Image.open(ROOT/clip['atlas'].removeprefix('res://')).crop((128*i,0,128*(i+1),128)).convert('RGBA')
        pending={(x,y) for y in range(128) for x in range(128) if im.getpixel((x,y))[3]};components=[]
        while pending:
            q=[pending.pop()];comp=[]
            while q:
                xy=q.pop();comp.append(xy)
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        p=(xy[0]+dx,xy[1]+dy)
                        if p in pending:pending.remove(p);q.append(p)
            components.append(comp)
        for comp in sorted(components,key=len,reverse=True)[1:]:
            rows=[]
            for x,y in sorted(comp):
                owners=[]
                for part in sorted(parts,key=lambda p:p['z']):
                    t=pose['part_transforms'][part['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
                    px=x+.5-t['position'][0];py=y+.5-t['position'][1]
                    u=(d*px-c*py)/det+part['pivot'][0];v=(-b*px+a*py)/det+part['pivot'][1]
                    xy=(math.floor(u),math.floor(v));center=(xy[0]+.5,xy[1]+.5)
                    if not (0<=xy[0]<128 and 0<=xy[1]<128):continue
                    owned=(not part['polygon'] or inside(center,part['polygon'])) and not any(inside(center,p) for p in part['exclude'])
                    if owned and src.getpixel(xy)[3]:owners.append([part['id'],xy,list(src.getpixel(xy))])
                rows.append(dict(destination=[x,y],owners=owners))
            print(json.dumps(dict(action=clip['action'],frame=i,count=len(comp),pixels=rows)))
