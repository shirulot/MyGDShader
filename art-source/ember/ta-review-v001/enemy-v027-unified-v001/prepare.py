"""只写TA隔离目录，验证V027完整ZIP及160条已批准来源。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import json,hashlib,re
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_sequences_eight_directions_v027_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-sequences-eight-directions-v027-review-v001';P=OUT/'technical-cold-load'
sha=lambda b:hashlib.sha256(b).hexdigest()
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert ZIP.stat().st_size==69253900 and sha(ZIP.read_bytes())=='aba87363a03247ab5069dc2d21dac9544a29e200932d86f0d7aa2a8a12e91826'
with ZipFile(ZIP) as z:
 assert z.testzip() is None and len(z.namelist())==1255
 files=json.loads(z.read('manifest.json'))['files'];assert len(files)==1254 and set(files)|{'manifest.json'}==set(z.namelist())
 for n,r in files.items():
  b=z.read(n);assert sha(b)==r['sha256']and len(b)==r['bytes']and (FIXED/n).read_bytes()==b,(n,'manifest')
 assert not P.exists()
 for n in z.namelist():
  target=P/n;assert target.resolve().is_relative_to(P.resolve());target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
assert not (P/'.godot').exists()
r=js(P/'assembly_recipe.json');cat=js(P/'output/catalog.json');accept=js(P/'TA_ACCEPTANCE.json')
assert sha((P/'output/catalog.json').read_bytes())=='0fdf47aebbce4c56aeed2c7baac9d13af77d3baaad71453a1abd9cf0bf8c1732'
assert r==cat and r['source_packages']==accept['source_packages']
units=['enemy_patrol','enemy_tracked_heavy','enemy_cutter','enemy_scout_drone'];dirs=['down','down_left','left','up_left','up','up_right','right','down_right'];spec={'idle':(4,4,True),'move':(8,8,True),'attack':(6,10,False),'hit':(4,12,False),'death':(8,10,False)}
assert r['units']==units and r['directions']==dirs and r['canvas']==[128,128]and r['root']==[64,104]
assert len(r['clips'])==160 and len(accept['clips'])==160 and len(r['source_packages'])==17
assert {(c['unit'],c['action'])for c in r['clips']}=={(u,a+'_'+d)for u in units for a in spec for d in dirs}
packages={};reports=[];records=[]
for h,p in r['source_packages'].items():
 b=(P/p['zip']).read_bytes();assert sha(b)==h
 original=ROOT/'art-source/ember/deliveries'/Path(p['zip']).name;assert original.read_bytes()==b
 packages[h]=ZipFile(BytesIO(b));assert packages[h].testzip() is None
 report=(P/p['included_review']).read_bytes();assert sha(report)==p['review_sha256']and (ROOT/p['review_report']).read_bytes()==report
 reports.append({'sha256':h,'report':p['review_report'],'included_review_byte_exact':True,'hash_mentioned_in_report':h in report.decode('utf-8-sig'),'heading':report.decode('utf-8-sig').splitlines()[0]})
for c in r['clips']:
 u,a=c['unit'],c['action'];kind=a.split('_')[0];n,fps,loop=spec[kind]
 assert (c['frame_count'],c['fps'],c['loop'])==(n,fps,loop)and a==kind+'_'+c['direction']
 ar=next(x for x in accept['clips']if x['unit']==u and x['action']==a)
 assert all(ar[k]==c[k]for k in ar)
 z=packages[c['source_zip_sha256']];oldcat=json.loads(z.read(c['source_catalog']));oldclips=[x for x in oldcat['clips']if x['action']==a and x.get('unit',u)==u];assert len(oldclips)==1
 old=oldclips[0]
 for key in ['frame_count','fps','loop','atlas_sha256','frame_hashes']:assert c[key]==old[key],(u,a,key)
 path=c['atlas'].removeprefix('res://');assert path==f'output/{u}/{a}.png'
 b=(P/path).read_bytes();assert b==z.read(old['atlas'].removeprefix('res://'))and sha(b)==c['atlas_sha256']
 atlas=np.array(Image.open(BytesIO(b)).convert('RGBA'));assert atlas.shape==(128,128*n,4)
 for i in range(n):
  fp=Path(path).with_suffix('')/f'f{i:02d}.png';oldfp=Path(old['atlas'].removeprefix('res://')).with_suffix('')/fp.name
  fb=(P/fp).read_bytes();assert fb==z.read(oldfp.as_posix()) and sha(fb)==c['frame_hashes'][i]
  arr=np.array(Image.open(BytesIO(fb)).convert('RGBA'));assert np.array_equal(arr,atlas[:,i*128:(i+1)*128]) and set(np.unique(arr[:,:,3]))<=set([0,255])
 records.append({'unit':u,'action':a,'source_zip_sha256':c['source_zip_sha256'],'frame_count':n,'frames_atlas_byte_exact':True})
 if u=='enemy_scout_drone'and c['direction']=='down':assert old['reviewed_zip']=='enemy_drone_actions_v011_2026-10-06.zip'and old['reviewed_zip_sha256']=='13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e'
tres=[]
for u in units:
 p=P/'output'/f'{u}.tres';s=p.read_text();paths=re.findall(r'\[ext_resource type="Texture2D" path="([^"]+)"',s)
 assert len(paths)==40 and len(set(paths))==40 and 'PackedByteArray'not in s
 for f in paths:assert not Path(f).is_absolute()and not f.startswith('res://')and (p.parent/f).is_file()
 tres.append({'unit':u,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'relative_atlases':len(paths)})
result={'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'payloads':1254,'manifest_sha256':sha((P/'manifest.json').read_bytes()),'catalog_sha256':sha((P/'output/catalog.json').read_bytes()),'source_packages':reports,'clips':records,'frames':sum(c['frame_count']for c in records),'unchanged_pngs':1120,'tres':tres,'initial_cache_absent':True}
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(records),'clips',result['frames'],'frames,17 sourceZIPs/reports,1120 original PNGs')
print(json.dumps(reports,ensure_ascii=False,indent=2))
