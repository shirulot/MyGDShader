"""Read-only, exact v002-to-v003 impact audit. No image edits."""
from pathlib import Path
from PIL import Image
import hashlib, json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'enemy-heavy-attack-death-v019-review-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
changes=[];unchanged=[];failures=[]
for clip in catalog['clips']:
    path=Path(clip['atlas'].removeprefix('res://')).with_suffix('')
    for index in range(clip['frame_count']):
        relative=path/f'f{index:02}.png'
        before=Image.open(OLD/relative).convert('RGBA')
        after=Image.open(ROOT/relative).convert('RGBA')
        pixels=[dict(xy=[x,y],before=list(before.getpixel((x,y))),after=list(after.getpixel((x,y))))
                for y in range(128) for x in range(128) if before.getpixel((x,y))!=after.getpixel((x,y))]
        if pixels:
            changes.append(dict(action=clip['action'],frame=index,count=len(pixels),pixels=pixels))
            if clip['direction'] not in ['down_left','right']:failures.append(str(relative))
        else:
            unchanged.append(str(relative))
            if sha(OLD/relative)!=sha(ROOT/relative):failures.append('RGBA same but PNG bytes changed: '+str(relative))
    if clip['direction'] not in ['down_left','right'] and sha(OLD/path.with_suffix('.png'))!=sha(ROOT/path.with_suffix('.png')):
        failures.append('Unaffected atlas changed: '+clip['action'])
source_unchanged=all(sha(p)==sha(OLD/p.relative_to(ROOT)) for p in (ROOT/'source').glob('*.png'))
assert source_unchanged
report=dict(status='PASS' if not failures else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),
            baseline_zip_sha256='c16edaeb70592d03cd8426a584399d815bb00fd7791e3242a606abdf9ff8d192',
            source_images_byte_identical=source_unchanged,changed_frames=changes,unchanged_frames=unchanged,failures=failures,
            fixes=['SW source (46,76)/(46,77) now fixed receiver ownership',
                   'E fixed socket clipped to x92..94, y73..86; source RGB and all poses unchanged'])
(ROOT/'qa/revision_audit_v003.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],changed=[{k:r[k] for k in ['action','frame','count']} for r in changes],unchanged=len(unchanged),failures=failures)))
raise SystemExit(bool(failures))
