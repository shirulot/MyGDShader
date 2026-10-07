"""Read-only RGBA/alpha/component audit; never modifies production art."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[]
binds=[]
preserved=[]
for clip in catalog['clips']:
    atlas_path=ROOT/clip['atlas'].removeprefix('res://')
    atlas=Image.open(atlas_path).convert('RGBA')
    assert sha(atlas_path)==clip['atlas_sha256']
    for index in range(clip['frame_count']):
        path=atlas_path.with_suffix('')/f'f{index:02}.png'
        frame=Image.open(path).convert('RGBA')
        alpha=frame.getchannel('A')
        pending={(x,y) for y in range(128) for x in range(128) if alpha.getpixel((x,y))}
        components=[]
        while pending:
            stack=[pending.pop()]; count=0
            while stack:
                x,y=stack.pop(); count+=1
                for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                    point=(x+dx,y+dy)
                    if point in pending:pending.remove(point);stack.append(point)
            components.append(count)
        bbox=alpha.getbbox()
        equal=frame.tobytes()==atlas.crop((index*128,0,(index+1)*128,128)).tobytes()
        safe=bbox is not None and bbox[0]>0 and bbox[1]>0 and bbox[2]<128 and bbox[3]<128
        binary=set(alpha.getdata())=={0,255}
        passed=equal and safe and binary and len(components)==1 and sha(path)==clip['frame_hashes'][index]
        records.append(dict(action=clip['action'],frame=index,atlas_equal=equal,bbox=bbox,
                            binary_alpha=binary,components=sorted(components,reverse=True),passed=passed))
    direction=clip['direction']
    if direction in spec['configs']:
        source=Image.open(ROOT/f'source/{direction}.png').convert('RGBA')
        bind=Image.open(ROOT/f'qa/bind_{direction}.png').convert('RGBA')
        changes=sum(a!=b for a,b in zip(source.getdata(),bind.getdata()))
        binds.append(dict(direction=direction,changed_rgba_pixels=changes,passed=changes==0))
for clip in spec['preserved']:
    path=ROOT/'output/enemy_cutter'/f"{clip['action']}.png"
    passed=sha(path)==clip['atlas_sha256'] and all(sha(path.with_suffix('')/f'f{i:02}.png')==h for i,h in enumerate(clip['frame_hashes']))
    preserved.append(dict(action=clip['action'],passed=passed))
passed=all(r['passed'] for r in records+binds+preserved)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),frames=records,binds=binds,preserved=preserved)
(ROOT/'qa/pixel_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(status=report['status'],frames=len(records),binds=binds,preserved=preserved,
                     failures=[r for r in records if not r['passed']])))
raise SystemExit(0 if passed else 1)
