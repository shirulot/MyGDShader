"""Read-only verification of boot-rim ownership, visible sole probes and change scope."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'enemy-patrol-profile-move-v021-review-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        cross=(p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0])
        if abs(cross)<1e-9 and min(a[0],b[0])-1e-9<=p[0]<=max(a[0],b[0])+1e-9 and min(a[1],b[1])-1e-9<=p[1]<=max(a[1],b[1])+1e-9:return True
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
ownership=[]
for kind,side,points in [('near','right',[(61,94),(61,95)]),('far','left',[(64,91),(64,92)])]:
    cfg=spec['configs']['right'];im=Image.open(ROOT/cfg[kind+'_source'].removeprefix('res://')).convert('RGBA')
    for x,y in points:
        owners=[p['id'] for p in cfg['parts'] if p['source_kind']==kind and inside((x+.5,y+.5),p['polygon']) and not any(inside((x+.5,y+.5),q) for q in p['exclude'])]
        assert owners==[side+'_foot'],(x,y,owners)
        ownership.append(dict(instance=kind,source_pixel=[x,y],rgba=im.getpixel((x,y)),owner=owners[0]))
records=[];probes=[]
for clip in catalog['clips']:
    changes=[]
    for i in range(clip['frame_count']):
        rel=Path('output/enemy_patrol')/clip['action']/f'f{i:02}.png'
        a,b=Image.open(OLD/rel).convert('RGBA'),Image.open(ROOT/rel).convert('RGBA')
        n=sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
        if n:changes.append(dict(frame=i,rgba_pixels=n))
        if clip['direction'] in spec['configs']:
            cfg=spec['configs'][clip['direction']]
            for side,leg in cfg['legs'].items():
                part=next(p for p in cfg['parts'] if p['id']==side+'_foot')
                source=Image.open(ROOT/cfg[part['source_kind']+'_source'].removeprefix('res://')).convert('RGBA')
                p=leg['visible_sole_source_pixel_center'];pixel=[math.floor(v) for v in p]
                rgba=source.getpixel(tuple(pixel));assert rgba[3]==255
                t=clip['poses'][i]['part_transforms'][part['id']]
                delta=[p[j]-part['pivot'][j] for j in (0,1)]
                q=[t['position'][j]+delta[0]*t['basis_x'][j]+delta[1]*t['basis_y'][j] for j in (0,1)]
                visible=b.getpixel(tuple(math.floor(v) for v in q))==rgba
                probes.append(dict(action=clip['action'],frame=i,side=side,source_pixel=pixel,actual_foot_pixel_center=q,source_rgba=rgba,visible=visible,nominal_sole=clip['poses'][i]['supports'][side]['sole']))
    assert clip['direction']=='right' or not changes,clip['action']
    records.append(dict(action=clip['action'],changes=changes,byte_identical=not changes))
sources={p.name:sha(p)==sha(OLD/'source'/p.name) for p in (ROOT/'source').glob('c002_*.png')}
assert all(sources.values())
report=dict(status='PASS',catalog_sha256=sha(ROOT/'output/catalog.json'),previous_zip_sha256='c5e82a238abaf9c0d258370322c02503cc320364cacca7f17d7b59547925481b',source_png_unchanged=sources,boot_rim_ownership=ownership,frame_changes=records,visible_sole_probes=probes,limits='Nominal sole is kinematic metadata. Actual opaque source probes are separate; a probe can be occluded by another fixed part. No new sole pixels were drawn.')
(ROOT/'qa/revision_v003.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status='PASS',changed_frames=sum(len(r['changes']) for r in records),rgba_changes=sum(c['rgba_pixels'] for r in records for c in r['changes']),visible_sole_probes=sum(p['visible'] for p in probes),total_sole_probes=len(probes))))
