"""Freeze the four-direction candidate; unused profile-leg studies are excluded."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-cutter-directions-move-v022-review-v002'
ZIP=ROOT.parent/'deliveries/enemy_cutter_six_moves_v022_v002_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/cutter-six-moves-v022-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB]),'Frozen version exists'
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    target=PACKAGE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
for name in ['project.godot','rig.gd','rig.json','masked_part.gdshader','export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','pixel_audit.py','pose_audit.py','inspect_actions.gd','previews/index.html']:
    copy(ROOT/name,name)
for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:
    copy(ROOT/'source'/f'{direction}.png',f'source/{direction}.png')
for folder in ['output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json'] and 'receipt' not in path.name:copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
for name in ['source/turnarounds/enemy_cutter_eight_views_v001.png','prompts/enemy_cutter_eight_views_v001.txt','registration.json']:
    copy(W/name,Path('provenance')/name)
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
receipt=dict(static_review='art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md',static_unit='enemy_cutter',
             down_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',down_right_zip_sha256='5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef',
             source_png_hashes={p.name:sha(p) for p in (PACKAGE/'source').glob('*.png')},new_actions=[c['action'] for c in catalog['clips'] if c['status']=='PENDING_TA_REVIEW'])
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text((ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=6,new_frames=48,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files+[PACKAGE/'manifest.json']:archive.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,item in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==item['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for p in (PACKAGE/folder).rglob('*.png'):
        target=WEB/p.relative_to(PACKAGE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
delivery=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/cutter-six-moves-v022-v002/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v002.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='web_hashes'}))
