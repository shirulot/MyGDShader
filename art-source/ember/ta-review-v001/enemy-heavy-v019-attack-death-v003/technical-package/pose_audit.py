"""Read-only endpoint, ground-support, and protected track-pixel audit."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[]
def inside(x,y,poly):
    result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result
for clip in catalog['clips']:
    folder=ROOT/'output/enemy_tracked_heavy'/clip['action']
    images=[Image.open(folder/f'f{i:02}.png').convert('RGBA') for i in range(clip['frame_count'])]
    endpoint=images[0].tobytes()==images[-1].tobytes() if clip['action'].startswith('attack_') else images[-2].tobytes()==images[-1].tobytes()
    config=spec['configs'].get(clip['direction'])
    changed=[]
    if config:
        source=Image.open(ROOT/'source'/f"{clip['direction']}.png").convert('RGBA')
        for y in range(128):
            for x in range(128):
                if not source.getpixel((x,y))[3]:continue
                if any(inside(x+.5,y+.5,p) for p in config['track_polygons']) and not inside(x+.5,y+.5,config['gun']['polygon']):
                    for i,im in enumerate(images):
                        if im.getpixel((x,y))!=source.getpixel((x,y)):changed.append([i,x,y])
    rigid=True
    for pose in clip['poses']:
        x,y=pose['gun_basis_x'],pose['gun_basis_y']
        rigid=rigid and abs(math.hypot(*x)-1)<1e-5 and abs(math.hypot(*y)-1)<1e-5
    # Protected pixels directly verify tread support, beyond unchanged metadata.
    records.append(dict(action=clip['action'],endpoint_equal=endpoint,barrel_rigid=rigid,track_pixels_changed=changed,passed=endpoint and rigid and not changed))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=hashlib.sha256((ROOT/'output/catalog.json').read_bytes()).hexdigest(),records=records)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],actions=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(0 if passed else 1)
