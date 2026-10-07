"""核对作者发布到本地预览目录的文件与冻结包，不修改网页。"""
from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-cold-load'
WEB=ROOT/'art-source/ember/enemy-sequences-v001/previews/enemy-eight-directions-v027-v001'
mapping={'index.html':'previews/index.html','catalog.json':'output/catalog.json'}
mapping.update({p.relative_to(P).as_posix():p.relative_to(P).as_posix()for p in (P/'output').rglob('*.png')})
records=[]
for web,source in mapping.items():
 b=(WEB/web).read_bytes();assert b==(P/source).read_bytes(),web
 records.append({'web':web,'frozen_source':source,'sha256':hashlib.sha256(b).hexdigest()})
cat=json.loads((P/'output/catalog.json').read_text())
for c in cat['clips']:
 if c['action'].startswith('idle_'):assert (P/'output'/c['unit']/('neutral_'+c['direction']+'.png')).read_bytes()==(P/'output'/c['unit']/c['action']/'f00.png').read_bytes()
(OUT/'technical-web-binding.json').write_text(json.dumps({'status':'PASS','files':records,'neutral_thumbnails_exact':32},indent=2))
print('PASS',len(records),'web bindings and32 neutral=idleF0')
