"""Read-only source ownership, rigid motion, and complete native-RGBA reconstruction."""
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
        if abs((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]))<1e-9 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]):return True
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
ownership=[];records=[]
for clip in catalog['clips']:
    d=clip['direction']
    if d not in spec['configs']:continue
    cfg=spec['configs'][d];im=Image.open(ROOT/f'source/{d}.png').convert('RGBA')
    masks={p['id']:[] for p in cfg['parts']};masks['body']=[];duplicates=[]
    for y in range(128):
        for x in range(128):
            color=im.getpixel((x,y))
            if not color[3]:continue
            protected=any(inside((x+.5,y+.5),p) for p in cfg['protected_body_polygons'])
            ids=[] if protected else [p['id'] for p in cfg['parts'] if inside((x+.5,y+.5),p['polygon'])]
            if len(ids)>1:duplicates.append([x,y,ids])
            for key in ids or ['body']:masks[key].append((x,y,color))
    ownership.append(dict(direction=d,duplicates=duplicates,part_pixels={k:len(v) for k,v in masks.items()},hidden_legs=cfg['hidden_legs'],passed=not duplicates))
    definitions={p['id']:p for p in cfg['parts']}
    for index,pose in enumerate(clip['poses']):
        actual=Image.open(ROOT/f'output/enemy_cutter/{clip["action"]}/f{index:02}.png').convert('RGBA')
        # Integer rigid transforms allow independent exact reconstruction without a renderer.
        expected={};rigid=True;body_changes=0
        for key,points in masks.items():
            t=pose['part_transforms'][key];pivot=definitions[key]['pivot'] if key!='body' else [0,0]
            rigid &= t['basis_x']==[1,0] and t['basis_y']==[0,1]
            dx,dy=[round(t['position'][j]-pivot[j]) for j in [0,1]]
            for x,y,color in points:
                dest=(x+dx,y+dy)
                expected[dest]=color
                if key=='body' and actual.getpixel(dest)!=color:body_changes+=1
        # Godot Color.TRANSPARENT is transparent WHITE; retain its RGB in the comparison.
        differences=[];visible_links=[]
        for y in range(128):
            for x in range(128):
                pixel=actual.getpixel((x,y));old=expected.get((x,y),(255,255,255,0))
                if pixel==old:continue
                valid=[]
                for key,poly in pose['socket_polygons'].items():
                    if not inside((x+.5,y+.5),poly):continue
                    sx,sy,w,h=definitions[key]['socket']['source_rect']
                    palette={im.getpixel((sx+dx,sy+dy)) for dx in range(w) for dy in range(h)}
                    if pixel in palette:valid.append(key)
                if not old[3] and valid:visible_links.append([x,y,valid])
                else:differences.append((x,y))
        contact=all(s['sole'] is None or not s['support'] or math.dist(s['sole'],s['ground'])<1e-6 for s in pose['supports'].values())
        sole_pixels=[]
        for key,s in pose['supports'].items():
            if s['sole'] is not None:
                x,y=map(int,s['sole']);sole_pixels.append(dict(id=key,alpha=actual.getpixel((x,y-1))[3]))
        passed=rigid and not differences and not body_changes and contact and all(p['alpha']==255 for p in sole_pixels)
        records.append(dict(action=clip['action'],frame=index,all_parts_rigid=rigid,unexplained_rgba_differences=differences,visible_dark_connector_pixels=visible_links,changed_body_source_pixels=body_changes,support_sole_matches_ground=contact,actual_sole_alpha=sole_pixels,passed=passed))
passed=all(r['passed'] for r in records+ownership)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),ownership=ownership,records=records)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],records=len(records),ownership_failures=[r for r in ownership if not r['passed']],failures=[r for r in records if not r['passed']])))
raise SystemExit(not passed)
