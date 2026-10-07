"""C22 完整只读解包；基于已读 preview 的 8 neutral+8 move 配置最小探针。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];PREV=OUT.with_name('enemy-patrol-v020-four-moves-v002')
ZIP=ROOT/'art-source/ember/deliveries/enemy_cutter_six_moves_v022_v002_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-cutter-directions-move-v022-review-v002'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==2549668 and sha(ZIP.read_bytes())=='3b1619b3cc5a32f11dbe699716b88a9b4a1b8874da55526d6d8c61f6e7d3377e'
z=ZipFile(ZIP);assert z.testzip() is None and len(z.namelist())==179
m=json.loads(z.read('manifest.json'));assert len(m['files'])==178 and set(z.namelist())==set(m['files'])|{'manifest.json'}
assert sha(z.read('output/catalog.json'))=='4bf5dfb6cdaec70a47b0cd4ea5e0fcb4bc5954b9ae57872fd6beebc8cf98e121'
for n,r in m['files'].items():
    b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
for folder in ['technical-package','technical-cold-load']:
    p=OUT/folder;assert not p.exists()
    for n in z.namelist():
        f=p/n;assert f.resolve().is_relative_to(p.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
probe=(PREV/'technical-cold-probe.gd').read_text(encoding='utf-8')
probe=probe.replace('size()!=6','size()!=8').replace('\tif sf.has_animation("move_left") or sf.has_animation("move_right"):\n\t\terrors.append("unmade W/E wrongly present")\n','')
probe=probe.replace('size()!=14','size()!=16').replace('8 neutral + 6 moves','8 neutral + 8 moves')
probe=probe.replace('["up_right"]','["down_left","left","up_left","up","up_right","right"]').replace('6 moves / 48 embedded frames','8 moves / 64 embedded frames').replace('9 NE CPU ownership masks and 8 NE pose readbacks','24 source ownership masks and 48 poses plus 18 sockets UV/bind geometry')
needle='\t\tvar poses:Array=[]'
insert='''\t\tvar socket_info:Array=[]
\t\tfor id:String in rig.sockets:
\t\t\tvar link:Polygon2D=rig.sockets[id]
\t\t\tvar uv:Array=[]
\t\t\tvar vertices:Array=[]
\t\t\tfor v:Vector2 in link.uv:uv.append([v.x,v.y])
\t\t\tfor v:Vector2 in link.polygon:vertices.append([v.x,v.y])
\t\t\tsocket_info.append({"id":id,"z":link.z_index,"filter":link.texture_filter,"uv":uv,"bind_polygon":vertices})
'''
probe=probe.replace(needle,insert+needle).replace('"masks":masks,"poses":poses','"masks":masks,"poses":poses,"sockets":socket_info')
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8');(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
(OUT/'technical-cold.py').write_text((PREV/'technical-cold.py').read_text(encoding='utf-8').replace('P20','C22').replace('NE CPU','six-direction CPU'),encoding='utf-8')
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'manifest_payloads':178,'zip_members':179,'crc_bad':None,'manifest_sha256':sha(z.read('manifest.json')),'catalog_sha256':sha(z.read('output/catalog.json')),'fixed_directory_payload_byte_exact':True,'files':m['files']}
(OUT/'technical-zip-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:178 payloads bound; complete cold copy and confirmed16-cache probe prepared.')
