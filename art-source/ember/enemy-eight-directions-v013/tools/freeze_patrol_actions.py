"""Freeze one complete seven-direction patrol batch; immutable destinations only."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
arg=argparse.ArgumentParser();arg.add_argument('batch',choices=['idle-hit-v025','attack-death-v026']);arg.add_argument('--version',default='v001');a=arg.parse_args()
BASE=Path(__file__).resolve().parents[2]
ROOT=BASE/f'enemy-patrol-{a.batch}'
PACKAGE=BASE/f'enemy-patrol-{a.batch}-review-{a.version}'
ZIP=BASE/'deliveries'/f'enemy_patrol_{a.batch.replace("-","_")}_{a.version}_2026-10-07.zip'
WEB=BASE/'enemy-sequences-v001/previews'/f'patrol-{a.batch}-{a.version}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in (PACKAGE,ZIP,WEB)),'Frozen destination exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
assert len(catalog['clips'])==16
assert sum(c['status']=='PENDING_TA_REVIEW' for c in catalog['clips'])==14
for n in ['pixel_audit','pose_audit','gpu_roundtrip','runtime']:
    q=json.loads((ROOT/'qa'/f'{n}.json').read_text(encoding='utf-8'))
    assert q['status']=='PASS' and q['catalog_sha256']==sha(ROOT/'output/catalog.json'),n
PACKAGE.mkdir()
def copy(p,rel):
    q=PACKAGE/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for p in ROOT.iterdir():
    if p.is_file() and (p.suffix in ['.gd','.gdshader','.tscn','.json','.md'] or p.name=='project.godot' or p.name in ['pixel_audit.py','pose_audit.py','build.py','build_web.py']):copy(p,p.name)
copy(ROOT/'previews/index.html','previews/index.html')
for folder in ['source','output','reference','qa']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and p.suffix in ['.png','.tres','.json'] and 'receipt' not in p.name:copy(p,p.relative_to(ROOT))
W=BASE/'enemy-eight-directions-v013'
for n in ['source/turnarounds/enemy_patrol_remaining_five_v004.png','source/turnarounds/enemy_patrol_calibration_v002.png','prompts/enemy_patrol_remaining_five_v004.txt','prompts/enemy_patrol_calibration_v002.txt','static_preflight_v002_patrol/registration.json','calibration_registration_v002.json']:
    copy(W/n,Path('provenance')/n)
copy(BASE/'enemy-patrol-profile-calibration-v021-c002-review-v003/calibration.json','provenance/calibration_c002_v003.json')
receipt=dict(static_review='art-source/ember/ta-review-v001/enemy-patrol-v013-s002/review-static.md',
             move_review='art-source/ember/ta-review-v001/enemy-patrol-v020-four-moves-v002/review-patrol-moves.md',
             profile_move_review='art-source/ember/ta-review-v001/enemy-patrol-v021-profile-move-v003/review-profile-moves.md',
             down_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',
             se_zip_sha256='c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21',
             four_move_zip_sha256='7bc4982abe5fdcfb7a205ddae599cffade57961b347fcd6200bb2f59a1f244a7',
             profile_move_zip_sha256='4e7bf6c2dc794ec64bb576c74b5755d4f08c9b8d5703c9dd4f15703c4a1c5a95',
             profile_calibration_zip_sha256='87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2',
             source_png_hashes={p.relative_to(PACKAGE/'source').as_posix():sha(p) for p in (PACKAGE/'source').rglob('*.png')})
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
fresh=[c for c in catalog['clips'] if c['status']=='PENDING_TA_REVIEW']
manifest=dict(status='PENDING_TA_REVIEW',new_clips=len(fresh),new_frames=sum(c['frame_count'] for c in fresh),preserved_clips=2,
              files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files+[PACKAGE/'manifest.json']:z.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as z:
    for n,m in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for p in (PACKAGE/folder).rglob('*.png'):
        q=WEB/p.relative_to(PACKAGE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
delivery=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url=f'http://127.0.0.1:6106/patrol-{a.batch}-{a.version}/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa'/f'submission_receipt_{a.version}.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='web_hashes'}))
