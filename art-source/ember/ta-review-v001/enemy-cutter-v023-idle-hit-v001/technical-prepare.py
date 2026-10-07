"""完整解包 C23 并绑定全部载荷；生产与冻结目录只读。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_cutter_idle_hit_v023_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-cutter-idle-hit-v023-review-v001'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==2864441 and sha(ZIP.read_bytes())=='ec2c8806c16271f55ee584749abe0166ac80e00985816150feb2b2369e934973'
z=ZipFile(ZIP);assert z.testzip() is None and len(z.namelist())==220
m=json.loads(z.read('manifest.json'));assert len(m['files'])==219 and set(z.namelist())==set(m['files'])|{'manifest.json'}
assert sha(z.read('output/catalog.json'))=='940b855cafd4c427e98ab2e0e3080ded092c4dd0cdd03c36e01a06aa224662ad'
for n,r in m['files'].items():
    b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
for folder in ['technical-package','technical-cold-load']:
    p=OUT/folder;assert not p.exists()
    for n in z.namelist():
        f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
(OUT/'technical-cold-load/ta_probe.gd').write_bytes((OUT/'technical-cold-probe.gd').read_bytes())
prior=OUT.with_name('enemy-cutter-v022-six-moves-v002')
(OUT/'technical-cold.py').write_text((prior/'technical-cold.py').read_text(encoding='utf-8').replace('C22','C23'),encoding='utf-8')
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':219,'zip_members':220,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:219 payloads bound; complete cold copy prepared.')
