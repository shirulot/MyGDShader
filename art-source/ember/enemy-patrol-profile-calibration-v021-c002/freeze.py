"""Static calibration only: original/candidate and actual assembled part exports."""
from pathlib import Path
from PIL import Image
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for d,probe in [('left',(66,94)),('right',(59,94))]:
    src=Image.open(ROOT/f'source/{d}.png').convert('RGBA');out=Image.open(ROOT/f'output/neutral_{d}.png').convert('RGBA')
    changes=[(x,y) for y in range(128) for x in range(128) if src.getpixel((x,y))!=out.getpixel((x,y))]
    assert len(changes)==(49 if d=='left' else 50)
    assert all(50<=x<77 and 78<=y<103 for x,y in changes)
    assert all(src.getpixel((x,103))==out.getpixel((x,103)) for x in range(128))
    assert src.getpixel(probe)==out.getpixel(probe)
    for name in ['near','far']:
        image=Image.open(ROOT/f'output/{d}_{name}.png').convert('RGBA');pending={(x,y) for y in range(128) for x in range(128) if image.getpixel((x,y))[3]};groups=[]
        while pending:
            queue=[pending.pop()];n=0
            while queue:
                x,y=queue.pop();n+=1
                for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                    if (x+dx,y+dy) in pending:pending.remove((x+dx,y+dy));queue.append((x+dx,y+dy))
            groups.append(n)
        assert len(groups)==1,(d,name,groups)
    records.append(dict(direction=d,changed_rgba_pixels=len(changes),coordinates=changes,bottom_row_equal=True,shin_probe=list(probe),shin_original_rgba=src.getpixel(probe),shin_candidate_rgba=out.getpixel(probe),source_sha256=sha(ROOT/f'source/{d}.png'),candidate_sha256=sha(ROOT/f'output/neutral_{d}.png')))
(ROOT/'qa/calibration_audit.json').write_text(json.dumps(dict(status='PASS',scope='static only, no new clips',records=records),indent=2),encoding='utf-8')
package=ROOT.parent/'enemy-patrol-profile-calibration-v021-c002-review-v003'
zip_path=ROOT.parent/'deliveries/enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip'
web=ROOT.parent/'enemy-sequences-v001/previews/patrol-profile-calibration-c002-v003'
assert not any(p.exists() for p in [package,zip_path,web])
package.mkdir();web.mkdir()
for name in ['project.godot','masked_part.gdshader','export.gd','calibration.json','README.md','index.html','preview.gd','preview.tscn']:
    shutil.copy2(ROOT/name,package/name)
for folder in ['source','output','qa']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and p.suffix in ['.png','.json'] and 'receipt' not in p.name:
            target=package/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
receipt=dict(status='STATIC_CALIBRATION_PENDING_TA',static_review='art-source/ember/ta-review-v001/enemy-patrol-v013-s002/review-static.md',static_zip_sha256='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1',source_instance_note='Two explicit physical legs share the same direction original visible near-leg design. No mirroring or new generated RGB.')
(package/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
files=sorted(p for p in package.rglob('*') if p.is_file())
manifest=dict(status='STATIC_CALIBRATION_PENDING_TA',new_clips=0,files={p.relative_to(package).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(package/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files+[package/'manifest.json']:archive.write(p,p.relative_to(package).as_posix())
for p in package.rglob('*'):
    if p.is_file() and (p.suffix=='.png' or p.name=='index.html'):
        target=web/p.relative_to(package);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
delivery=dict(zip=str(zip_path),zip_sha256=sha(zip_path),bytes=zip_path.stat().st_size,payload_count=len(files),url='http://127.0.0.1:6106/patrol-profile-calibration-c002-v003/index.html',new_clips=0)
(ROOT/'qa/submission_receipt_v003.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print(json.dumps(delivery))
