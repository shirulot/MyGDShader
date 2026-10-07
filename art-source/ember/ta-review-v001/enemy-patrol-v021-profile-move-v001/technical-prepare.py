"""完整解包 P21 候选，仅在 TA 副本内运行最小 cold。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
PREV=OUT.with_name('enemy-patrol-v020-four-moves-v002')
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_profile_moves_v021_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-patrol-profile-move-v021-review-v001'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==3688508 and sha(ZIP.read_bytes())=='4c907f50f6851787d84e7212a0cd7c64215566baf482a520fde937212db10b61'
z=ZipFile(ZIP);assert z.testzip() is None and len(z.namelist())==124
m=json.loads(z.read('manifest.json'));assert len(m['files'])==123 and set(z.namelist())==set(m['files'])|{'manifest.json'}
assert sha(z.read('output/catalog.json'))=='b9d5126648a815db4d8a3d13bfba3d848389ae5695a3cd3ade1089c0eb799480'
for n,r in m['files'].items():
    b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
for folder in ['technical-package','technical-cold-load']:
    p=OUT/folder;assert not p.exists()
    for n in z.namelist():
        f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
probe=(PREV/'technical-cold-probe.gd').read_text(encoding='utf-8')
probe=probe.replace('size()!=6','size()!=4').replace('sf.has_animation("move_left") or sf.has_animation("move_right")','sf.has_animation("move_up") or sf.has_animation("move_down_left") or sf.has_animation("move_up_left") or sf.has_animation("move_up_right")').replace('unmade W/E wrongly present','out-of-batch directions wrongly present')
probe=probe.replace('size()!=14','size()!=20').replace('8 neutral + 6 moves','8 original + 8 neutral + 4 moves')
probe=probe.replace('["up_right"]','["left","right"]').replace('6 moves / 48 embedded frames','4 moves / 32 embedded frames').replace('9 NE CPU ownership masks and 8 NE pose readbacks','18 W/E CPU ownership masks and 16 W/E pose readbacks')
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8');(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
(OUT/'technical-cold.py').write_text((PREV/'technical-cold.py').read_text(encoding='utf-8').replace('P20','P21').replace('NE CPU','W/E CPU'),encoding='utf-8')
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':123,'zip_members':124,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:123 payload ZIP/manifest/fixed-directory bound; complete cold copy prepared.')
