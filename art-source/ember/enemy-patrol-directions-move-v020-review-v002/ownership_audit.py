"""Read-only ownership uniqueness and v001 revision-scope audit."""
from pathlib import Path
from PIL import Image
import json,hashlib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'enemy-patrol-directions-move-v020-review-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
records=[];failures=[]
for direction,cfg in spec['configs'].items():
    source=Image.open(ROOT/cfg['source'].removeprefix('res://')).convert('RGBA')
    duplicates=[];stretchable=[]
    for y in range(128):
        for x in range(128):
            if not source.getpixel((x,y))[3]:continue
            center=(x+.5,y+.5)
            if any(inside(center,p) for p in cfg['protected_body_polygons']):continue
            owners=[p['id'] for p in cfg['parts'] if inside(center,p['polygon']) and not any(inside(center,e) for e in p['exclude'])]
            if len(owners)>1:duplicates.append(dict(source=[x,y],owners=owners))
            if direction=='up_right' and 'left_thigh' in owners:stretchable.append(dict(source=[x,y],rgba=list(source.getpixel((x,y)))))
    if duplicates:failures.append(direction+' duplicate ownership')
    if any(min(p['rgba'][:3])>100 for p in stretchable):failures.append('NE pale armor in left_thigh')
    records.append(dict(direction=direction,duplicates=duplicates,ne_left_thigh_sources=stretchable))
changes=[];unchanged=[]
for clip in catalog['clips']:
    rel=Path(clip['atlas'].removeprefix('res://'))
    for i in range(8):
        p=rel.with_suffix('')/f'f{i:02}.png'
        if sha(ROOT/p)==sha(OLD/p):unchanged.append(str(p))
        else:
            a=Image.open(OLD/p).convert('RGBA');b=Image.open(ROOT/p).convert('RGBA')
            pixels=[dict(xy=[x,y],before=list(a.getpixel((x,y))),after=list(b.getpixel((x,y)))) for y in range(128) for x in range(128) if a.getpixel((x,y))!=b.getpixel((x,y))]
            changes.append(dict(action=clip['action'],frame=i,count=len(pixels),pixels=pixels))
            if clip['direction']!='up_right':failures.append('Unexpected change '+str(p))
    if clip['direction']!='up_right' and sha(ROOT/rel)!=sha(OLD/rel):failures.append('Unexpected atlas '+str(rel))
sources_same=all(sha(p)==sha(OLD/p.relative_to(ROOT)) for p in (ROOT/'source').glob('*.png') if (OLD/p.relative_to(ROOT)).exists())
assert sources_same
report=dict(status='PASS' if not failures else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),ownership=records,changed_frames=changes,unchanged_frames=unchanged,source_images_byte_identical=sources_same,failures=failures)
(ROOT/'qa/ownership_revision_v002.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],changed=[{k:c[k] for k in ['action','frame','count']} for c in changes],unchanged=len(unchanged),duplicates={r['direction']:len(r['duplicates']) for r in records},failures=failures)))
raise SystemExit(bool(failures))
