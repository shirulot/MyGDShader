"""Freeze the complete assembly and its original review archives without overwriting."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-sequences-eight-directions-v027-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_sequences_eight_directions_v027_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/enemy-eight-directions-v027-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in (PACKAGE,ZIP,WEB)),'Frozen version exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
assert len(catalog['clips'])==160 and sum(c['frame_count'] for c in catalog['clips'])==960
assert all(c['status'] in ['TA_APPROVED','PRESERVED_TA_APPROVED'] for c in catalog['clips'])
for name in ['gpu_roundtrip','runtime']:
    q=json.loads((ROOT/'qa'/f'{name}.json').read_text(encoding='utf-8'))
    assert q['status']=='PASS' and q['catalog_sha256']==sha(ROOT/'output/catalog.json'),name
q=json.loads((ROOT/'qa/assembly_integrity.json').read_text(encoding='utf-8'))
assert q['status']=='PASS' and q['frame_count']==960 and q['recipe_sha256']==sha(ROOT/'assembly_recipe.json')
PACKAGE.mkdir()
def copy(p,rel):
    q=PACKAGE/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for p in ROOT.iterdir():
    if p.is_file() and (p.suffix in ['.gd','.tscn','.json','.md','.py'] or p.name=='project.godot'):copy(p,p.name)
copy(ROOT/'previews/index.html','previews/index.html')
for folder in ['output','qa','reviewed_packages','review_reports']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and p.suffix in ['.png','.tres','.json','.zip','.md'] and (folder!='qa' or 'receipt' not in p.name):copy(p,p.relative_to(ROOT))
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='ALL_INDIVIDUAL_ART_APPROVED_ASSEMBLY_PENDING_TA_REVIEW',clips=160,frames=960,units=4,preserved_down_clips=20,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files+[PACKAGE/'manifest.json']:z.write(p,p.relative_to(PACKAGE).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix=='.zip' else zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(ZIP) as z:
    for n,m in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for p in (PACKAGE/'output').rglob('*.png'):
    q=WEB/p.relative_to(PACKAGE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
receipt=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/enemy-eight-directions-v027-v001/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
