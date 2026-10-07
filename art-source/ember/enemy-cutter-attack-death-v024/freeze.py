"""Freeze exact review bytes only after export, rendering, playback and pixel checks."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-cutter-attack-death-v024-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/cutter-attack-death-v024-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB])
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
for filename in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
 q=json.loads((ROOT/'qa'/filename).read_text(encoding='utf-8'))
 assert q['status']=='PASS' and q['catalog_sha256']==sha(ROOT/'output/catalog.json'),filename
PACKAGE.mkdir()
def copy(p,r):
 q=PACKAGE/r;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for n in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json','part.gdshader','export.gd','verify.gd','capture.gd','pixel_audit.py','pose_audit.py','inspect_actions.gd','inspect_parts.gd','previews/index.html','README.md']:copy(ROOT/n,n)
for folder in ['source','output','reference','qa']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.png','.tres','.json'] and not p.name.startswith('submission_receipt'):copy(p,p.relative_to(ROOT))
previous=ROOT.parent/'enemy-eight-directions-v013'
for name in ['source/turnarounds/enemy_cutter_eight_views_v001.png','prompts/enemy_cutter_eight_views_v001.txt','registration.json']:copy(previous/name,Path('provenance')/name)
copy(ROOT.parent/'enemy-eight-directions-v013-pilot-hc-v001/output/enemy_cutter/rig_neutral_down_right.png','provenance/approved_hc_neutral.png')
assert sha(PACKAGE/'provenance/approved_hc_neutral.png')==sha(ROOT/'source/down_right.png')
receipt=dict(static_review='art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md',move_review='art-source/ember/ta-review-v001/enemy-cutter-v022-six-moves-v002/review-cutter-moves.md',idle_hit_review='art-source/ember/ta-review-v001/enemy-cutter-v023-idle-hit-v001/review-idle-hit.md',down_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',se_first_gate_zip_sha256='5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef',source_png_hashes={p.name:sha(p) for p in (ROOT/'source').glob('*.png')},new_actions=[c['action'] for c in catalog['clips'] if c['status']=='PENDING_TA_REVIEW'])
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=14,new_frames=98,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files+[PACKAGE/'manifest.json']:z.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as z:
 for name,m in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==m['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
 for p in (PACKAGE/folder).rglob('*.png'):
  q=WEB/p.relative_to(PACKAGE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
receipt=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),new_actions=receipt['new_actions'],url='http://127.0.0.1:6106/cutter-attack-death-v024-v001/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
