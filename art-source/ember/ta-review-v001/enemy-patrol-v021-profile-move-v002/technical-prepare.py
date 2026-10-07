"""P21 v002 完整绑定与最小冷副本；仅在新 TA 目录写入。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];PREV=OUT.with_name('enemy-patrol-v021-profile-move-v001')
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_profile_moves_v021_v002_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-patrol-profile-move-v021-review-v002'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==2883551 and sha(ZIP.read_bytes())=='c5e82a238abaf9c0d258370322c02503cc320364cacca7f17d7b59547925481b'
with ZipFile(ZIP) as z:
    assert z.testzip() is None and len(z.namelist())==131
    m=json.loads(z.read('manifest.json'));assert len(m['files'])==130 and set(z.namelist())==set(m['files'])|{'manifest.json'}
    assert sha(z.read('output/catalog.json'))=='bd3f70e183fad3c713c59c2e5336c7915903810f57896528426c09b330f24b10'
    for name,row in m['files'].items():
        data=z.read(name);assert sha(data)==row['sha256'] and len(data)==row['bytes'] and data==(FIXED/name).read_bytes()
    for folder in ['technical-package','technical-cold-load']:
        p=OUT/folder;assert not p.exists()
        for name in z.namelist():
            f=p/name;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))
    result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'payloads':130,'members':131,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_byte_equal':True,'files':m['files']}
probe=(PREV/'technical-cold-probe.gd').read_text(encoding='utf-8')
# Current preview was read: it deliberately caches8 original+8neutral+4move clips.
assert 'size()!=20' in probe
probe=probe.replace('var poses:Array=[]','var bind_transforms:Dictionary={}\n\t\trig.reset_bind()\n\t\tfor id:String in rig.parts:\n\t\t\tvar tr:Transform2D=rig.parts[id].transform\n\t\t\tbind_transforms[id]={"position":[tr.origin.x,tr.origin.y],"basis_x":[tr.x.x,tr.x.y],"basis_y":[tr.y.x,tr.y.y]}\n\t\tvar poses:Array=[]')
probe=probe.replace('"masks":masks,"poses":poses','"masks":masks,"bind_transforms":bind_transforms,"poses":poses')
needle='mask.save_png(path)'
replacement='''mask.save_png(path)
			var source_path:String=rig.config.body_source
			if id!="body":
				for part:Dictionary in rig.config.parts:
					if part.id==id:source_path=rig.config[part.source_kind+"_source"]
			var expected_image:=Image.load_from_file(ProjectSettings.globalize_path(source_path))
			expected_image.convert(Image.FORMAT_RGBA8)
			var actual_image:Image=sprite.texture.get_image()
			actual_image.convert(Image.FORMAT_RGBA8)
			if expected_image.get_data()!=actual_image.get_data():errors.append("actual part texture "+direction+" "+id)'''
assert needle in probe;probe=probe.replace(needle,replacement)
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8');(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
runner=(OUT.with_name('enemy-cutter-v024-attack-death-v001')/'technical-cold.py').read_text(encoding='utf-8')
(OUT/'technical-cold.py').write_text(runner,encoding='utf-8')
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
# Baseline contains the independent phase/segment math; the next TA patch adds C002 binding.
audit=(PREV/'technical-audit.py').read_text(encoding='utf-8').replace("textures={'canonical':arr(P/c['source'].removeprefix('res://'))", "textures={'canonical':arr(P/c['body_source'].removeprefix('res://'))")
audit=audit.replace('Near/far are declared physical instances reusing generated directional leg parts, not two independently drawn sources and not zero-difference S002 bind.','Near/far are fixed C002 same-source physical instances; unique ownership is measured within each instance only.')
audit=audit.replace('TECHNICAL_LOAD_AND_POSE_PASS_IDENTITY_P2_SEPARATE','TECHNICAL_BASELINE_PASS_C002_EXTENSION_PENDING').replace('New generated side legs replace original S002 visible geometry; binding is intentionally not RGBA0. Raw/prompt/register and209/213ROI addressed by identity agent. Technical consistency cannot override identity P2.','Uses approved C002 body/near/far. Bind against C002 must be RGBA0; historical S00249/50 changes remain. Static approval does not prove motion.')
(OUT/'technical-audit.py').write_text(audit,encoding='utf-8')
print('PASS130 payloads; cold and independent baseline prepared.')
