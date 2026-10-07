"""完整冻结包/原336载荷绑定；新建独立运行副本，绝不执行生产导出脚本。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/robot_collect_knee_v012_rc01_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/robot-eight-way-v011/revisions/collect-knee-v012'
OLDZIP=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_final_2026-10-07.zip'
OLD=ROOT/'art-source/ember/robot-eight-way-v011/delivery/robot-v011'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(ZIP.read_bytes())=='4dc7298a4b1f3782635bd461eca6dc2be1179e79b35dc4ecfa7ac04a6030f209' and ZIP.stat().st_size==14181428
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    m=json.loads(z.read('sha256-manifest.json'));assert len(m['files'])==698
    assert sha(z.read('sha256-manifest.json'))=='86214fe22664b7ceaeced7084cd4fd111a5dc5147a0b58869a8ca23cb9614890'
    listed={r['file']:r for r in m['files']};assert set(z.namelist())==set(listed)|{'sha256-manifest.json'}
    for name,r in listed.items():
        b=z.read(name);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and b==(FIXED/name).read_bytes()
    for folder in ['technical-package','technical-cold-load']:
        p=OUT/folder;assert not p.exists()
        for name in z.namelist():
            f=p/name;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))
assert sha(OLDZIP.read_bytes())=='8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb'
with ZipFile(OLDZIP) as z:
    old=json.loads(z.read('sha256-manifest.json'));assert len(old['files'])==336
    for r in old['files']:
        b=z.read(r['file']);assert sha(b)==r['sha256'] and b==(OLD/r['file']).read_bytes()
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'payloads':698,'members':699,'manifest_sha256':sha((FIXED/'sha256-manifest.json').read_bytes()),'fixed_directory_byte_equal':True,'baseline_zip_sha256':sha(OLDZIP.read_bytes()),'baseline_frozen_payload_unchanged':336,'files':m['files']}
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS698 candidate payload and336 baseline frozen payloads; complete cold copy prepared.')
