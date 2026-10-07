"""绑定完整 C24 ZIP，创建 TA 独立副本，原冻结包保持只读。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v002_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-cutter-attack-death-v024-review-v002'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==3807029 and sha(ZIP.read_bytes())=='3fc81f650daf58c949f216c4b9a783b03348d9ba11fcf512f7e6f08f92ff80be'
with ZipFile(ZIP) as z:
    assert z.testzip() is None and len(z.namelist())==329
    m=json.loads(z.read('manifest.json'));assert len(m['files'])==328 and set(z.namelist())==set(m['files'])|{'manifest.json'}
    assert sha(z.read('output/catalog.json'))=='fd2bf874e376a4ec7194e975a45c3b47a9cbee471ee6a09591b3fb5534f11a70'
    for n,r in m['files'].items():
        b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
    for folder in ['technical-package','technical-cold-load']:
        p=OUT/folder;assert not p.exists()
        for n in z.namelist():
            f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
    result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':328,'zip_members':329,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-cold-load/ta_probe.gd').write_bytes((OUT/'technical-cold-probe.gd').read_bytes())
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:328 payloads bound; complete cold copy prepared.')
