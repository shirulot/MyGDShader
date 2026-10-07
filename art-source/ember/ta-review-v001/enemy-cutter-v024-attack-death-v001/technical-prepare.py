"""绑定完整 C24 ZIP，创建 TA 独立副本，原冻结包保持只读。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-cutter-attack-death-v024-review-v001'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==3802515 and sha(ZIP.read_bytes())=='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c'
with ZipFile(ZIP) as z:
    assert z.testzip() is None and len(z.namelist())==327
    m=json.loads(z.read('manifest.json'));assert len(m['files'])==326 and set(z.namelist())==set(m['files'])|{'manifest.json'}
    assert sha(z.read('output/catalog.json'))=='444e71fa6255dc25e5eb824a882c58bb07f94ba444364df20eac1039b1e99a7c'
    for n,r in m['files'].items():
        b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
    for folder in ['technical-package','technical-cold-load']:
        p=OUT/folder;assert not p.exists()
        for n in z.namelist():
            f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
    result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':326,'zip_members':327,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-cold-load/ta_probe.gd').write_bytes((OUT/'technical-cold-probe.gd').read_bytes())
prior=OUT.with_name('enemy-cutter-v023-idle-hit-v001')
# Reuse the cold runner, with a terminating editor import for this scene.
(OUT/'technical-cold.py').write_text((prior/'technical-cold.py').read_text(encoding='utf-8').replace("'--editor','--import'","'--editor','--import','--quit'"),encoding='utf-8')
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:326 payloads bound; complete cold copy prepared.')
