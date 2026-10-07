"""Read-only checks. New lower-leg calibration is explicit, not a zero-difference bind."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
records=[];binds=[];preserved=[];ownership=[]

def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit

for clip in catalog['clips']:
    path=ROOT/clip['atlas'].removeprefix('res://');atlas=Image.open(path).convert('RGBA')
    assert sha(path)==clip['atlas_sha256']
    for index in range(8):
        p=path.with_suffix('')/f'f{index:02}.png';im=Image.open(p).convert('RGBA');alpha=im.getchannel('A')
        pending={(x,y) for y in range(128) for x in range(128) if alpha.getpixel((x,y))};components=[]
        while pending:
            stack=[pending.pop()];n=0
            while stack:
                x,y=stack.pop();n+=1
                for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                    q=(x+dx,y+dy)
                    if q in pending:pending.remove(q);stack.append(q)
            components.append(n)
        bbox=alpha.getbbox();binary=set(alpha.getdata())=={0,255}
        equal=im.tobytes()==atlas.crop((128*index,0,128*(index+1),128)).tobytes()
        safe=bbox is not None and min(bbox[:2])>0 and max(bbox[2:])<128
        passed=binary and equal and safe and len(components)==1 and sha(p)==clip['frame_hashes'][index]
        records.append(dict(action=clip['action'],frame=index,bbox=bbox,binary_alpha=binary,atlas_equal=equal,components=components,passed=passed))
for direction,cfg in spec['configs'].items():
    source=Image.open(ROOT/f'source/{direction}.png').convert('RGBA');bind=Image.open(ROOT/f'qa/bind_{direction}.png').convert('RGBA')
    changes=[(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))!=bind.getpixel((x,y))]
    # 两腿校准区域一次固定在髋部以下；原身躯、头部和工具必须保持源像素。
    outside=[p for p in changes if not (50<=p[0]<77 and 78<=p[1]<105)]
    tools=[(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3] and any(inside((x+.5,y+.5),q) for q in cfg['protected_body_polygons'])]
    changed_tools=[p for p in tools if source.getpixel(p)!=bind.getpixel(p)]
    neutral=Image.open(ROOT/f'output/enemy_patrol/neutral_{direction}.png').convert('RGBA')
    binds.append(dict(direction=direction,scope='Two lower legs replaced with fixed master; requires visual calibration approval',changed_rgba_pixels=len(changes),changed_coordinates=changes,allowed_rect=[50,78,27,27],outside_scope=outside,changed_tool_pixels=changed_tools,neutral_equals_actual_bind=neutral.tobytes()==bind.tobytes(),passed=not outside and not changed_tools and neutral.tobytes()==bind.tobytes()))
    # near/far 是明确声明的两个物理实例，内部零件各自只拥有一次源像素。
    for kind in ['near','far']:
        im=Image.open(ROOT/cfg[kind+'_source'].removeprefix('res://')).convert('RGBA')
        duplicate=[];unowned=[]
        for y in range(128):
            for x in range(128):
                if not im.getpixel((x,y))[3]:continue
                owners=[p['id'] for p in cfg['parts'] if p['source_kind']==kind and inside((x+.5,y+.5),p['polygon']) and not any(inside((x+.5,y+.5),q) for q in p['exclude'])]
                if len(owners)>1:duplicate.append([x,y,owners])
                if not owners:unowned.append([x,y])
        ownership.append(dict(direction=direction,instance=kind,duplicate=duplicate,unowned=unowned,passed=not duplicate and not unowned))
for clip in spec['preserved']:
    path=ROOT/'output/enemy_patrol'/f"{clip['action']}.png"
    passed=sha(path)==clip['atlas_sha256'] and all(sha(path.with_suffix('')/f'f{i:02}.png')==h for i,h in enumerate(clip['frame_hashes']))
    preserved.append(dict(action=clip['action'],passed=passed))
passed=all(r['passed'] for r in records+binds+preserved+ownership)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),frames=records,binds=binds,preserved=preserved,ownership=ownership)
(ROOT/'qa/pixel_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],frames=len(records),bind_changes=[(b['direction'],b['changed_rgba_pixels'],b['outside_scope'],b['changed_tool_pixels']) for b in binds],failures=[r for r in records+ownership if not r['passed']])))
raise SystemExit(not passed)
