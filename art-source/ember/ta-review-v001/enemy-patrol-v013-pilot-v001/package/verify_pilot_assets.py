"""Read-only pixel audit of native exports; writes a JSON report, never images."""
from pathlib import Path
from collections import deque
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def image(path):return Image.open(path).convert('RGBA')
def components(im):
    alpha=im.getchannel('A')
    points={(x,y) for y in range(128) for x in range(128) if alpha.getpixel((x,y))>=128}
    sizes=[]
    while points:
        pending=[points.pop()];count=0
        while pending:
            x,y=pending.pop();count+=1
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                p=x+dx,y+dy
                if p in points:points.remove(p);pending.append(p)
        sizes.append(count)
    return sorted(sizes,reverse=True)

catalog_path=ROOT/'output/pilot_catalog_v013.json'
catalog=json.loads(catalog_path.read_text())
rig_spec=json.loads((ROOT/'pilot_rigs.json').read_text())
source_by_unit={item['unit']:item['source'] for item in rig_spec['units']}
records=[];bindings=[];passed=True
for clip in catalog['clips']:
    unit=clip['unit'];atlas_path=ROOT/clip['atlas'][6:];atlas=image(atlas_path)
    assert sha(atlas_path)==clip['atlas_sha256']
    assert sha(ROOT/clip['tres'][6:])==clip['tres_sha256']
    for index in range(8):
        path=ROOT/f'output/{unit}/move_down_right/f{index:02}.png'
        im=image(path);raw=im.tobytes();alpha=set(im.getchannel('A').getdata())
        matched=sha(path)==clip['frame_hashes'][index]
        atlas_diff=sum(a!=b for a,b in zip(raw,atlas.crop((index*128,0,(index+1)*128,128)).tobytes()))
        islands=components(im)
        bbox=im.getchannel('A').getbbox()
        safe=bbox[0]>0 and bbox[1]>0 and bbox[2]<128 and bbox[3]<128
        okay=matched and atlas_diff==0 and alpha<={0,255} and safe and len(islands)==1
        passed &= okay
        records.append(dict(unit=unit,frame=index,sha_match=matched,atlas_differing_channels=atlas_diff,alpha=sorted(alpha),components=islands,bbox=bbox,pass_check=okay))
    original=image(ROOT/source_by_unit[unit].removeprefix('res://'))
    bind=image(ROOT/f'output/{unit}/rig_neutral_down_right.png')
    changed=[(x,y)for y in range(128)for x in range(128)if original.getpixel((x,y))!=bind.getpixel((x,y))]
    visible_changed=[(x,y) for x,y in changed if original.getpixel((x,y))[3]!=0 or bind.getpixel((x,y))[3]!=0]
    if unit=='enemy_tracked_heavy':
        bind_ok=not changed
        note='Full bind RGBA equals original registered static master.'
    elif unit=='enemy_cutter':
        def in_front_regions(p):
            x,y=p
            return 43<=x<59 and 80<=y<97 or 71<=x<86 and 77<=y<96
        unexpected=[p for p in changed if not in_front_regions(p)]
        bind_ok=not unexpected
        note='Only two declared front-leg regions may change; original rear armor, hull and tools must remain unchanged.'
    elif unit=='enemy_patrol':
        bind_ok=not visible_changed
        note='Visible RGBA and coverage equal approved s002 direction exactly. Fully transparent source RGB is normalized to zero during export and is counted separately.'
    else:
        bind_ok=True;note='Pending separate source-specific visual checks.'
    passed &= bind_ok
    bindings.append(dict(unit=unit,changed_pixels=len(changed),visible_changed_pixels=len(visible_changed),pass_check=bind_ok,note=note,unexpected_pixels=unexpected if unit=='enemy_cutter' else []))
report=dict(status='PASS' if passed else 'FAIL',scope='Author pixel integrity audit, not TA approval',catalog_sha256=sha(catalog_path),frames=records,bind_pose_source_checks=bindings)
(ROOT/'qa/pilot_pixel_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(status=report['status'],frames=len(records),bind=bindings)))
raise SystemExit(0 if passed else 1)
