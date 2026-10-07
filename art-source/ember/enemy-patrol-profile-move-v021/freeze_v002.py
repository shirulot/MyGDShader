"""Freeze two profile moves with explicit lower-leg calibration evidence."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-patrol-profile-move-v021-review-v002'
ZIP=ROOT.parent/'deliveries/enemy_patrol_profile_moves_v021_v002_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/patrol-profile-moves-v021-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB]),'Frozen version exists'
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    target=PACKAGE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
for name in ['project.godot','rig.gd','rig.json','masked_part.gdshader','export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','pixel_audit.py','pose_audit.py','inspect_actions.gd','compare_bind.gd','previews/index.html']:
    copy(ROOT/name,name)
for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:
    copy(ROOT/'source'/f'{direction}.png',f'source/{direction}.png')
for direction in ['left','right']:
    for kind in ['body','near','far']:
        name=f'c002_{direction}_{kind}.png'
        copy(ROOT/'source'/name,Path('source')/name)
    name=f'c002_neutral_{direction}.png'
    copy(ROOT/'source'/name,Path('source')/name)
copy(ROOT.parent/'enemy-patrol-profile-calibration-v021-c002-review-v003/calibration.json','provenance/calibration_c002_v003.json')
for folder in ['output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json'] and 'receipt' not in path.name:copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
for name in ['source/turnarounds/enemy_patrol_remaining_five_v004.png','source/turnarounds/enemy_patrol_calibration_v002.png','prompts/enemy_patrol_remaining_five_v004.txt','prompts/enemy_patrol_calibration_v002.txt','static_preflight_v002_patrol/registration.json','calibration_registration_v002.json']:
    copy(W/name,Path('provenance')/name)
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
receipt=dict(calibration_zip_sha256='87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2',calibration_review='art-source/ember/ta-review-v001/enemy-patrol-v021-calibration-c002-v003/review-static-calibration.md',static_review='art-source/ember/ta-review-v001/enemy-patrol-v013-s002/review-static.md',static_zip_sha256='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1',
             down_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',down_right_zip_sha256='c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21',
             source_png_hashes={p.name:sha(p) for p in (PACKAGE/'source').glob('*.png')},new_actions=[c['action'] for c in catalog['clips'] if c['status']=='PENDING_TA_REVIEW'])
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text((ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=2,new_frames=16,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files+[PACKAGE/'manifest.json']:archive.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,item in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==item['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for p in (PACKAGE/folder).rglob('*.png'):
        target=WEB/p.relative_to(PACKAGE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
delivery=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/patrol-profile-moves-v021-v002/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v002.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='web_hashes'}))
