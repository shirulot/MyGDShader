"""Publish an immutable review snapshot and bind its exact bytes to the localhost player."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-cutter-idle-hit-v023-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_cutter_idle_hit_v023_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/cutter-idle-hit-v023-v001'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(),'Frozen destination exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
for filename in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    qa=json.loads((ROOT/'qa'/filename).read_text(encoding='utf-8'))
    assert qa['status']=='PASS' and qa['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()

def copy(path,relative):
    target=PACKAGE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)

for name in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json','move_rig.gd','move_rig.json','pilot_rig.gd','pilot_rigs.json','entity_cutout.gdshader',
             'masked_part.gdshader','export.gd','verify.gd','capture.gd','pixel_audit.py','inspect_actions.gd','pose_audit.py','previews/index.html']:
    copy(ROOT/name,name)
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json']:
            copy(path,path.relative_to(ROOT))
previous=ROOT.parent/'enemy-eight-directions-v013'
for filename in ['source/turnarounds/enemy_cutter_eight_views_v001.png','prompts/enemy_cutter_eight_views_v001.txt','registration.json']:
    copy(previous/filename,Path('provenance')/filename)
receipt={'static_review':'art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md',
         'down_zip_sha256':'42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',
         'se_first_gate_zip_sha256':'5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef',
         'source_png_hashes':{p.name:sha(p) for p in (ROOT/'source').glob('*.png')},
         'new_actions':[x['action'] for x in catalog['clips'] if x['status']=='PENDING_TA_REVIEW']}
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text((ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
copy(ROOT.parent/'enemy-eight-directions-v013-pilot-hc-v001/prompts/cutter_down_right_legs_v001.txt','provenance/cutter_down_right_legs_v001.txt')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest={'status':'PENDING_TA_REVIEW','new_clips':14,'new_frames':56,'preserved_clips':2,'files':{
    p.relative_to(PACKAGE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}}
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files+[PACKAGE/'manifest.json']:archive.write(path,path.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,data in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==data['sha256']
WEB.mkdir()
shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html')
shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for path in (PACKAGE/folder).rglob('*.png'):
        target=WEB/path.relative_to(PACKAGE)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
receipt={'zip':str(ZIP),'zip_sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'payload_count':len(files),
         'catalog_sha256':sha(PACKAGE/'output/catalog.json'),'new_actions':receipt['new_actions'],
         'url':'http://127.0.0.1:6106/cutter-idle-hit-v023-v001/index.html',
         'web_hashes':{p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()}}
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
