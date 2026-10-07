"""完整解包并绑定 P20 v002；审查副本写入独立目录。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
PREV=OUT.with_name('enemy-patrol-v020-four-moves-v001')
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_four_moves_v020_v002_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-patrol-directions-move-v020-review-v002'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==3225225 and sha(ZIP.read_bytes())=='7bc4982abe5fdcfb7a205ddae599cffade57961b347fcd6200bb2f59a1f244a7'
z=ZipFile(ZIP);assert z.testzip() is None and len(z.namelist())==145
m=json.loads(z.read('manifest.json'));assert len(m['files'])==144 and set(z.namelist())==set(m['files'])|{'manifest.json'}
assert sha(z.read('output/catalog.json'))=='6ff3f3d757485709d27f4c358bc113cbe3190f87e65464d9ae4071f1ac122f81'
for n,r in m['files'].items():
    b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
for folder in ['technical-package','technical-cold-load']:
    p=OUT/folder;assert not p.exists()
    for n in z.namelist():
        f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
audit=(PREV/'technical-audit.py').read_text(encoding='utf-8')
audit=audit.replace('if d in models:',"if d == 'up_right':")
audit=audit.replace("if c['direction'] in models}","if c['direction'] == 'up_right'}")
audit=audit.replace('all_32_pose_supports_exact','all_8_NE_pose_supports_exact')
(OUT/'technical-audit.py').write_text(audit,encoding='utf-8')
probe=(PREV/'technical-cold-probe.gd').read_text(encoding='utf-8')
probe=probe.replace('["down_left","up_left","up","up_right"]','["up_right"]')
probe=probe.replace('36 CPU ownership masks and 32 pose readbacks','9 NE CPU ownership masks and 8 NE pose readbacks')
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8')
(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':144,'zip_members':145,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS: ZIP, manifest, fixed directory bound; two complete copies extracted; reused CPU audit now reconstructs only changed NE.')
