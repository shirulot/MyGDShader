"""Read-only proof that only fan apertures change after declared whole-body hover."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[];axes=[]
for direction,config in spec['configs'].items():
    source=Image.open(ROOT/config['source'].removeprefix('res://')).convert('RGBA')
    colors={fan['id']:[] for fan in config['fans']}
    for index,dy in enumerate(spec['body_y']):
        frame=Image.open(ROOT/f'output/enemy_scout_drone/move_{direction}/f{index:02}.png').convert('RGBA')
        outside=[];alpha=[]
        for y in range(128):
            for x in range(128):
                value=frame.getpixel((x,y+dy)) if 0<=y+dy<128 else (0,0,0,0)
                old=source.getpixel((x,y))
                inside=any(sum(((v+.5-c)/r)**2 for v,c,r in zip([x,y],fan['center'],fan['radius']))<1 for fan in config['fans'])
                # Off-canvas padding is transparent. Its hidden RGB has no source sample
                # and must not be compared to PNG's stored transparent-white palette entry.
                if not inside and (value[3] or old[3]) and value!=old:outside.append([x,y])
                if value[3]!=old[3]:alpha.append([x,y])
        for fan in config['fans']:
            cx,cy=map(int,fan['center'])
            colors[fan['id']].append(frame.getpixel((cx,cy+dy)))
        records.append(dict(direction=direction,frame=index,hover_y=dy,outside_aperture_rgba_differences=len(outside),
                            alpha_differences=len(alpha),passed=not outside and not alpha))
    for fan,values in colors.items():axes.append(dict(direction=direction,fan=fan,colors=values,constant=len(set(values))==1))
passed=all(x['passed'] for x in records) and all(x['constant'] for x in axes)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=hashlib.sha256((ROOT/'output/catalog.json').read_bytes()).hexdigest(),
            scope='All alpha and visible RGBA outside apertures; transparent padding RGB is excluded',
            frame_checks=records,axis_checks=axes)
(ROOT/'qa/rotor_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],frames=len(records),stable_axes=sum(x['constant'] for x in axes),
                     frame_failures=[x for x in records if not x['passed']])))
raise SystemExit(0 if passed else 1)
