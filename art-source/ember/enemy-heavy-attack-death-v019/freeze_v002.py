"""Freeze an immutable attack/death candidate with local reproduction inputs."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-heavy-attack-death-v019-review-v002'
ZIP=ROOT.parent/'deliveries/enemy_heavy_attack_death_v019_v002_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/heavy-attack-death-v019-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB]),'Frozen version exists'
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    target=PACKAGE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
for path in ROOT.iterdir():
    if path.is_file() and path.suffix in ['.gd','.gdshader','.godot','.tscn','.json','.py'] and path.name != 'build.py' and not path.name.startswith('freeze'):
        copy(path,path.name)
copy(ROOT/'previews/index.html','previews/index.html')
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.json','.tres'] and 'receipt' not in path.name:
            copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
copy(W/'source/turnarounds/enemy_tracked_heavy_eight_views_v001.png','provenance/approved_heavy_views_v001.png')
copy(W/'registration.json','provenance/static_registration.json')
source_receipt=json.loads((ROOT.parent/'enemy-heavy-idle-hit-v015-review-v001/SOURCE_RECEIPT.json').read_text(encoding='utf-8'))
source_receipt['new_actions']=[c['action'] for c in json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))['clips'] if c['status']!='PRESERVED_TA_APPROVED']
source_receipt['hidden_master_sha256']=sha(ROOT/'source/hidden_chassis_eight_views_v001.png')
source_receipt['hidden_generation_exec']='6c53a6cb-d855-42b8-993e-cc01e8292426'
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(source_receipt,indent=2),encoding='utf-8')
copy(ROOT/'source/hidden_chassis_prompt.txt','source/hidden_chassis_prompt.txt')
(PACKAGE/'README.md').write_text((ROOT/'README_source.md').read_text(encoding='utf-8').replace('review v001','review v002')+'\n送审前元数据修订：SOURCE_RECEIPT的new_actions已从上一批idle/hit更正为当前attack/death。动画、源文件和catalog不变，v001未提交TA。\n',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=14,new_frames=98,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
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
receipt=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/heavy-attack-death-v019-v002/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v002.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
